class StateMachine:
    def __init__(self, tab_dict):
        self._gui_state = 0
        self._ker_state = {}
        for key in tab_dict.keys():
            self._ker_state[key] = 0

    @property 
    def gui_state(self):
        return self._gui_state
    
    @gui_state.setter
    def gui_state(self, new_state):
        if new_state > 3 or new_state < 0:
            raise ValueError("state not support")        
        if new_state == self.gui_state:
            return

        if new_state < self.gui_state:
            self._gui_state = new_state
            for key in self._ker_state.keys():
                self._ker_state[key] = 0
    
    @property
    def ker_state(self, kid):
        return self._ker_state[kid]
    
    @ker_state.setter
    def ker_state(self, kid, new_kstate):
        if not self.is_gui_ready:
            return
        if self.ker_state[kid] == new_kstate:
            return
    
    def is_gui_ready(self):
        return self.gui_state == 3
        
    

