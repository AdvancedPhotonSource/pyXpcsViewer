key = {
    "nexus": {
        # qmap related
        "mask": "/xpcs/qmap/mask",
        "dqmap": "/xpcs/qmap/dynamic_roi_map",
        "sqmap": "/xpcs/qmap/static_roi_map",
        "dqlist": "/xpcs/qmap/dynamic_v_list_dim0",
        "sqlist": "/xpcs/qmap/static_v_list_dim0",
        "dplist": "/xpcs/qmap/dynamic_v_list_dim1",
        "splist": "/xpcs/qmap/static_v_list_dim1",
        # the beam center is in the qmap is calibrated
        "bcy": "/xpcs/qmap/beam_center_y",
        "bcx": "/xpcs/qmap/beam_center_x",
        "det_dist": "/xpcs/qmap/detector_distance",
        "pixel_size": "/xpcs/qmap/pixel_size",
        "static_index_mapping": "/xpcs/qmap/static_index_mapping",
        "dynamic_index_mapping": "/xpcs/qmap/dynamic_index_mapping",
        "static_num_pts": "/xpcs/qmap/static_num_pts",
        "dynamic_num_pts": "/xpcs/qmap/dynamic_num_pts",
        "start_time": "/entry/start_time",
        "map_names": "/xpcs/qmap/map_names",
        "map_units": "/xpcs/qmap/map_units",
        # multitau related
        "Int_t": "/xpcs/spatial_mean/intensity_vs_time",
        "G2": "/xpcs/multitau/unnormalized_G2",
        "tau": "/xpcs/multitau/delay_list",
        "g2": "/xpcs/multitau/normalized_g2",
        "stride_frame": "/xpcs/multitau/config/stride_frame",
        "avg_frame": "/xpcs/multitau/config/avg_frame",
        "g2_err": "/xpcs/multitau/normalized_g2_err",
        "saxs_2d": "/xpcs/temporal_mean/scattering_2d",
        "saxs_1d": "/xpcs/temporal_mean/scattering_1d",
        "Iqp": "/xpcs/temporal_mean/scattering_1d_segments",
        "c2_g2_segments": "/xpcs/twotime/normalized_g2_segments",
        "c2_g2": "xpcs/twotime/normalized_g2",
        "c2_delay": "/xpcs/twotime/delay_list",
        "c2_prefix": "/xpcs/twotime/correlation_map",
        "c2_processed_bins": "/xpcs/twotime/processed_bins",
        "c2_stride_frame": "/xpcs/twotime/config/stride_frame",
        "c2_avg_frame": "/xpcs/twotime/config/avg_frame",
        "t0": "/entry/instrument/detector_1/frame_time",
        "t1": "/entry/instrument/detector_1/count_time",
        "X_energy": "/entry/instrument/incident_beam/incident_energy",
        # "ccdx": "/entry/instrument/detector_1/position_x",
        # "ccdy": "/entry/instrument/detector_1/position_y",
        # "ccdx0": "/entry/instrument/detector_1/beam_center_position_x",
        # "ccdy0": "/entry/instrument/detector_1/beam_center_position_y",
        "pix_dim_x": "/entry/instrument/detector_1/x_pixel_size",
        "pix_dim_y": "/entry/instrument/detector_1/y_pixel_size",
        # "bcx": "/entry/instrument/detector_1/beam_center_x",
        # "bcy": "/entry/instrument/detector_1/beam_center_y",
        # "det_dist": "/entry/instrument/detector_1/distance",
    }
}
