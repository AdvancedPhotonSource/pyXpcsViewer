# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""
Optimized script for efficiently averaging data from HDF5 files using a
shared memory-based map-reduce strategy with a real-time progress bar.

This script leverages Python's `multiprocessing.shared_memory` to allow worker
processes to write their results directly into pre-allocated RAM blocks,
completely avoiding disk I/O and IPC bottlenecks for large data transfer.

"""

import argparse
import glob
import logging
import multiprocessing
import os
import time
from multiprocessing import shared_memory

import h5py
import numpy as np
import psutil
import tqdm

# Import the key mapping and file writing utility from the user's custom module.
from .g2_utils import keymap, regroup_G2, save_G2_to_file

# --- Globals for Worker Processes ---
# These will be initialized by the pool's initializer function. This is the
# correct way to share non-picklable objects like locks with a process pool
# when using 'spawn' or 'forkserver' start methods.
g_progress_counter = None
g_progress_lock = None


def init_worker(counter, lock, level):
    """Initializer function for each worker process in the pool."""
    global g_progress_counter, g_progress_lock
    g_progress_counter = counter
    g_progress_lock = lock

    # Configure logging for each worker process
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_physical_core_count():
    """
    Determines the number of physical CPU cores. This is more reliable for
    CPU-bound tasks than using the logical core count from os.cpu_count().
    """
    return psutil.cpu_count(logical=False)


def is_valid_file(fname, avg_window, avg_qindex, avg_blmin, avg_blmax, always_valid=False):
    """
    Checks if a file is valid based on its G2 baseline within a given window and range.
    Returns (is_valid, g2_baseline).
    """
    try:
        with h5py.File(fname, "r", libver="latest") as fhdl:
            g2_data = fhdl[keymap["g2"]]
            idx_q = avg_qindex if avg_qindex < g2_data.shape[1] else g2_data.shape[1] - 1
            g2_baseline = np.mean(g2_data[-avg_window:, idx_q])
            if always_valid:
                return True, g2_baseline
            else:
                return avg_blmin <= g2_baseline <= avg_blmax, g2_baseline
    except Exception:
        return False, -1.0


def find_first_valid_file_and_dims(
    flist,
    avg_window,
    avg_qindex,
    avg_blmin,
    avg_blmax,
    processing_dtype,
    nonzero_G2=False,
    always_valid=False,
):
    """Reads files sequentially until it finds one that is valid to get data shapes."""
    logging.info("Searching for a valid file to determine array shapes for memory allocation...")
    for fname in flist:
        try:
            valid, g2_baseline = is_valid_file(fname, avg_window, avg_qindex, avg_blmin, avg_blmax)
            if valid:
                logging.info(f"Found valid file: {os.path.basename(fname)}")
                with h5py.File(fname, "r", libver="latest") as fhdl:
                    shapes = {}
                    dtypes = {}
                    for skey in ["G2", "saxs1d", "saxs1d_segments", "saxs2d"]:
                        dset = fhdl[keymap[skey]]
                        shapes[skey] = dset.shape
                        # FIX: Create a numpy.dtype object instance, not just a class
                        dtypes[skey] = np.dtype(processing_dtype)

                    # Add counter array for G2 valid pixel counting if nonzero_G2 is enabled
                    if nonzero_G2:
                        shapes["G2_count"] = shapes["G2"]
                        dtypes["G2_count"] = np.dtype(np.uint32)
                    return fname, shapes, dtypes
        except Exception:
            continue
    return None, None, None


def worker_process_chunk(args_tuple):
    """
    The "map" function. Processes a chunk of files, writes the sum directly
    into a dedicated shared memory block, and updates a shared progress counter.
    """
    flist_chunk, worker_args, worker_id, shm_metas = args_tuple
    (
        avg_window,
        avg_qindex,
        avg_blmin,
        avg_blmax,
        h5_cache_size_mb,
        verbose,
        nonzero_G2,
        always_valid,
    ) = worker_args

    logger = logging.getLogger(f"Worker-{worker_id:02d}")

    logger.debug(f"Started. Processing {len(flist_chunk)} files.")

    # Attach to the existing shared memory blocks
    shm_blocks = {key: shared_memory.SharedMemory(name=meta["name"]) for key, meta in shm_metas.items()}

    # Create numpy arrays that are views into the shared memory
    shm_arrays = {
        key: np.ndarray(meta["shape"], dtype=meta["dtype"], buffer=shm.buf)
        for (key, shm), meta in zip(shm_blocks.items(), shm_metas.values(), strict=False)
    }
    # Initialize this worker's memory block to zero
    for arr in shm_arrays.values():
        arr[:] = 0.0

    local_valid_files = 0
    first_valid_file_in_chunk = None
    skipped_files_in_chunk = []
    h5_cache_size_bytes = h5_cache_size_mb * 1024**2

    for i, fname in enumerate(flist_chunk):
        file_basename = os.path.basename(fname)
        try:
            valid, g2_baseline = is_valid_file(fname, avg_window, avg_qindex, avg_blmin, avg_blmax)
            if valid:
                if first_valid_file_in_chunk is None:
                    first_valid_file_in_chunk = fname

                with h5py.File(fname, "r", rdcc_nbytes=h5_cache_size_bytes, libver="latest") as fhdl:
                    if nonzero_G2:
                        # Load G2 data once and compute valid mask for efficiency
                        G2_data = fhdl[keymap["G2"]][()]
                        valid_mask = G2_data > 0

                        for skey, shm_arr in shm_arrays.items():
                            if skey == "G2":
                                # Accumulate G2 values (invalid pixels are 0, so just add all)
                                shm_arr += G2_data
                            elif skey == "G2_count":
                                # Count valid pixels for G2 averaging
                                shm_arr[valid_mask] += 1.0
                            else:
                                # NumPy correctly handles casting from file dtype to accumulator dtype
                                shm_arr += fhdl[keymap[skey]][()]
                    else:
                        # Original behavior: simple accumulation
                        for skey, shm_arr in shm_arrays.items():
                            # NumPy correctly handles casting from file dtype to accumulator dtype
                            shm_arr += fhdl[keymap[skey]][()]
                    local_valid_files += 1
            else:
                skipped_files_in_chunk.append((file_basename, g2_baseline))
        except Exception:
            skipped_files_in_chunk.append((file_basename, -1.0))

        # Increment the shared counter using the global variables
        with g_progress_lock:
            g_progress_counter.value += 1

    # Close the shared memory attachments, but don't unlink
    for shm in shm_blocks.values():
        shm.close()

    return (
        local_valid_files,
        first_valid_file_in_chunk,
        skipped_files_in_chunk,
        worker_id,
    )


def fast_average_shared_memory(
    flist,
    output_filename="averaged_results.hdf",
    avg_window=3,
    avg_qindex=0,
    avg_blmin=0.95,
    avg_blmax=1.30,
    num_workers=None,
    h5_cache_size_mb=512,
    verbose=False,
    precision="single",
    nonzero_G2=False,
    always_valid=False,
    progress_callback=None,
    status_callback=None,
):
    """Run G2 averaging across a file list using shared-memory map-reduce.

    Allocates per-worker shared memory, dispatches HDF5 reads to a process pool,
    and writes the averaged result back to *output_filename*.

    Args:
        flist: List of absolute paths to HDF5 result files.
        output_filename: Path for the averaged output file.
        avg_window: Number of trailing frames used for baseline calculation.
        avg_qindex: Q-index into G2 data for baseline evaluation.
        avg_blmin: Inclusive lower bound for valid G2 baseline.
        avg_blmax: Inclusive upper bound for valid G2 baseline.
        num_workers: Process count (default: physical CPU cores).
        h5_cache_size_mb: HDF5 raw chunk cache per worker in MB.
        verbose: Enable DEBUG-level logging.
        precision: ``"single"`` for float32 or ``"double"`` for float64 accumulation.
        nonzero_G2: Use per-pixel valid counting to exclude zero pixels.
        always_valid: Skip baseline checks and process all files.
        progress_callback: Callable ``(current, total)`` invoked every 0.1 s.
        status_callback: Callable with a single status-message string.

    Returns:
        ``None`` on empty input or no valid files; the output file is written in place.
    """
    if not flist:
        logging.warning("No files provided for averaging.")
        return

    def _report_status(msg: str) -> None:
        """Log a status message and forward it to the callback.

        Args:
            msg: Status message string.
        """
        logging.info(msg)
        if status_callback:
            status_callback(msg)

    # Determine processing precision
    processing_dtype = np.float32 if precision == "single" else np.float64
    _report_status(f"Using {precision} precision ({processing_dtype.__name__}) for processing.")

    first_file, shapes, dtypes = find_first_valid_file_and_dims(
        flist,
        avg_window,
        avg_qindex,
        avg_blmin,
        avg_blmax,
        processing_dtype,
        nonzero_G2,
        always_valid,
    )

    if not first_file:
        logging.error("Could not find any valid files to process. Aborting.")
        return

    # --- Worker Configuration ---
    if num_workers is None or num_workers <= 0:
        physical_cores = get_physical_core_count()
        logging.info(f"Detected {physical_cores} physical cores. Setting number of workers accordingly.")
        num_workers = physical_cores

    num_workers = min(num_workers, len(flist), os.cpu_count())
    logging.info(f"Using {num_workers} worker processes.")

    # --- Create a list of shared memory blocks, one for each worker ---
    all_shm_metas = []
    all_shm_blocks = []
    total_mem_gb = 0
    _report_status("Allocating shared memory blocks for worker results...")
    for i in range(num_workers):
        worker_shm_metas = {}
        worker_shm_blocks = {}
        for key in shapes:
            dtype = dtypes[key]
            shape = shapes[key]
            size = np.prod(shape) * dtype.itemsize
            total_mem_gb += size

            # Create the shared memory block
            shm = shared_memory.SharedMemory(create=True, size=size)
            worker_shm_metas[key] = {"name": shm.name, "shape": shape, "dtype": dtype}
            worker_shm_blocks[key] = shm
        all_shm_metas.append(worker_shm_metas)
        all_shm_blocks.append(worker_shm_blocks)
    logging.info(f"Successfully allocated {total_mem_gb / 1e9:.2f} GB of shared memory.")

    # --- Map Step ---
    file_chunks = np.array_split(flist, num_workers)
    worker_args = (
        avg_window,
        avg_qindex,
        avg_blmin,
        avg_blmax,
        h5_cache_size_mb,
        verbose,
        nonzero_G2,
        always_valid,
    )
    # The counter and lock are no longer passed in the tasks tuple
    tasks = [(chunk, worker_args, i + 1, all_shm_metas[i]) for i, chunk in enumerate(file_chunks) if chunk.size > 0]

    final_sum_result = {}
    total_valid_files = 0
    first_valid_file_path = None
    all_skipped_files = []

    # --- Create Shared Progress Counter ---
    progress_counter = multiprocessing.Value("i", 0)
    progress_lock = multiprocessing.Lock()

    _report_status("Starting file processing (map stage)...")

    main_start_time = time.time()
    try:
        # Pass the initializer function and its arguments to the Pool
        log_level = logging.DEBUG if verbose else logging.INFO
        pool_initargs = (progress_counter, progress_lock, log_level)
        with multiprocessing.Pool(processes=num_workers, initializer=init_worker, initargs=pool_initargs) as pool:
            # Use map_async for non-blocking execution
            result_async = pool.map_async(worker_process_chunk, tasks)

            total_files = len(flist)
            # Only show tqdm if no callback is provided
            if progress_callback is None:
                pbar = tqdm.tqdm(total=total_files, desc="Processing Files")
            else:
                pbar = None

            while not result_async.ready():
                current = progress_counter.value
                if progress_callback:
                    progress_callback(current, total_files)
                if pbar:
                    pbar.n = current
                    pbar.refresh()
                time.sleep(0.1)  # Update UI 10 times per second

            # Final update to make sure the bar reaches 100%
            current = progress_counter.value
            if progress_callback:
                progress_callback(current, total_files)
            if pbar:
                pbar.n = current
                pbar.refresh()
                pbar.close()

            # Now, get the results from the workers
            results = result_async.get()

        for local_count, local_first_valid, local_skipped, worker_id in results:
            logging.debug(f"Received metadata from Worker {worker_id:02d}")
            total_valid_files += local_count
            all_skipped_files.extend(local_skipped)
            if first_valid_file_path is None and local_first_valid is not None:
                first_valid_file_path = local_first_valid

        map_end_time = time.time()
        logging.info(f"Map stage completed in {map_end_time - main_start_time:.2f} seconds.")

        # --- Reduce Step (in main process from shared memory) ---
        _report_status("Starting result aggregation from shared memory (reduce stage)...")
        reduce_start_time = time.time()

        worker_results_in_ram = []
        for i in range(num_workers):
            worker_result = {
                key: np.ndarray(
                    meta["shape"],
                    dtype=meta["dtype"],
                    buffer=all_shm_blocks[i][key].buf,
                )
                for key, meta in all_shm_metas[i].items()
            }
            worker_results_in_ram.append(worker_result)

        # Sum the results from all workers
        for key in shapes:
            # Initialize the final sum with the result from the first worker's memory
            # Use a copy to avoid modifying the shared memory block directly
            sum_arr = worker_results_in_ram[0][key].copy()
            # Add the results from the remaining workers
            for i in range(1, num_workers):
                sum_arr += worker_results_in_ram[i][key]
            final_sum_result[key] = sum_arr

        logging.info(f"Reduce stage completed in {time.time() - reduce_start_time:.2f} seconds.")

        # --- Finalization and Output ---
        if total_valid_files > 0 and first_valid_file_path:
            _report_status("Calculating final average and saving to disk...")
            avg_result = {}
            for key, value in final_sum_result.items():
                if key == "G2" and nonzero_G2:
                    # Special handling for G2: divide by valid pixel counts
                    valid_counts = final_sum_result["G2_count"]
                    # Clip valid_counts to avoid division by zero
                    valid_counts_clipped = np.clip(valid_counts, a_min=1.0, a_max=None)
                    avg_result[key] = value / valid_counts_clipped
                    logging.info(
                        f"G2 averaging: using per-pixel valid counts (min: {valid_counts.min()}, max: {valid_counts.max()}, mean: {valid_counts.mean():.2f})"
                    )
                elif key == "G2_count":
                    # Don't include the count array in the final result
                    continue
                else:
                    # Standard averaging for other keys
                    avg_result[key] = value / total_valid_files

            try:
                # since the output_filename is already generated from the 1st part of g2 average;
                # we just need to apply the new G2 to the file
                assert os.path.exists(output_filename), (
                    f"output_filename: {output_filename} does not exist. check 1st part of g2 average."
                )
                # output_dir = os.path.dirname(output_filename)
                # if output_dir and not os.path.exists(output_dir):
                #     os.makedirs(output_dir)
                # shutil.copy(first_valid_file_path, output_filename)
                avg_result = regroup_G2(output_filename, avg_result)
                save_G2_to_file(output_filename, avg_result=avg_result)
                logging.info(f"Success: Averaged data saved to '{output_filename}'")
            except Exception:
                logging.exception("Error saving output file:")
        else:
            logging.warning("No files passed the baseline check. No averaging performed.")

        # --- Summary ---
        summary_lines = [
            "--- Summary ---",
            f"Total processing time: {time.time() - main_start_time:.2f} seconds.",
            f"Processed {len(flist)} files in total.",
            f"Found {total_valid_files} files that met the baseline criteria.",
        ]

        for line in summary_lines:
            _report_status(line)

        if all_skipped_files:
            _report_status(f"Skipped {len(all_skipped_files)} files.")
            for i, (fname, baseline) in enumerate(all_skipped_files[:5]):
                status = f"baseline {baseline:.4f}" if baseline != -1.0 else "read error"
                logging.info(f"  - Example Skipped: {fname} ({status})")
            if len(all_skipped_files) > 5:
                logging.info("  ...")

    finally:
        # --- Crucial Cleanup Step ---
        logging.info("Cleaning up shared memory blocks...")
        for worker_blocks in all_shm_blocks:
            for shm in worker_blocks.values():
                shm.close()
                shm.unlink()  # Free the memory
        logging.info("Cleanup complete.")


def main():
    """CLI entry point for the G2 averaging tool.

    Parses arguments from sys.argv and calls :func:`fast_average_shared_memory`.
    """
    # command line arguments
    parser = argparse.ArgumentParser(
        description="Average G2 data from HDF files using a shared-memory map-reduce strategy.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_path",
        help="A text file with a list of input HDF files (one per line), a folder containing *_result.hdf files, OR a path prefix (e.g., /path/to/folder/my_prefix to match my_prefix* files).",
    )
    parser.add_argument("-o", "--output", default="averaged_results.hdf", help="Output file name.")
    parser.add_argument(
        "--baseline-min",
        type=float,
        default=0.95,
        help="Minimum g2 baseline to include file.",
    )
    parser.add_argument(
        "--baseline-max",
        type=float,
        default=1.35,
        help="Maximum g2 baseline to include file.",
    )
    parser.add_argument(
        "--baseline-qindex",
        type=int,
        default=0,
        help="Q index for baseline calculation.",
    )
    parser.add_argument(
        "--baseline-window",
        type=int,
        default=3,
        help="Window size for baseline calculation.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Num worker processes (default: physical cores).",
    )
    parser.add_argument(
        "--cache-mb",
        type=int,
        default=512,
        help="HDF5 raw chunk cache per worker (in MB).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed, per-file diagnostic logging (DEBUG level).",
    )
    parser.add_argument(
        "--precision",
        type=str,
        default="single",
        choices=["single", "double"],
        help="Processing precision for accumulation (default: single).",
    )
    parser.add_argument(
        "--nonzero-G2",
        action="store_true",
        help="Enable per-pixel valid counting for G2 averaging (excludes zero/invalid pixels).",
    )
    parser.add_argument(
        "--always-valid",
        action="store_true",
        help="Ignore baseline criteria and treat all files as valid.",
    )
    args = parser.parse_args()

    # --- Configure Root Logger ---
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("--- Configuration ---")
    logging.info(f"Output file:           {args.output}")
    logging.info(f"Baseline range:        [{args.baseline_min}, {args.baseline_max}]")
    logging.info(f"Baseline Q-index:      {args.baseline_qindex}")
    logging.info(f"Baseline window:       {args.baseline_window}")
    logging.info(f"HDF5 cache per worker: {args.cache_mb} MB")
    logging.info(f"Processing Precision:  {args.precision}")
    logging.info(f"Nonzero G2 averaging:  {'Enabled' if args.nonzero_G2 else 'Disabled'}")
    logging.info(f"Always Valid Policy:   {'Enabled' if args.always_valid else 'Disabled'}")
    logging.info(f"Verbose Logging:       {'Enabled' if args.verbose else 'Disabled'}")
    logging.info("---------------------\n")

    # --- Generate file list ---
    input_path = args.input_path
    if os.path.isfile(input_path) and input_path.endswith(".txt"):
        with open(input_path) as f:
            flist = [line.strip() for line in f if line.strip()]
    elif os.path.isdir(input_path):
        flist = sorted(glob.glob(os.path.join(input_path, "*_result.hdf")))
    else:
        # Assume it's a prefix
        flist = sorted(glob.glob(input_path + "*"))

    if flist:
        fast_average_shared_memory(
            flist,
            output_filename=args.output,
            avg_window=args.baseline_window,
            avg_qindex=args.baseline_qindex,
            avg_blmin=args.baseline_min,
            avg_blmax=args.baseline_max,
            num_workers=args.num_workers,
            h5_cache_size_mb=args.cache_mb,
            verbose=args.verbose,
            precision=args.precision,
            nonzero_G2=args.nonzero_G2,
            always_valid=args.always_valid,
        )


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    if multiprocessing.get_start_method(allow_none=True) != "spawn":
        multiprocessing.set_start_method("spawn", force=True)
    main()
