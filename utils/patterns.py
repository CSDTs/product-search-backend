class State:
    """Base state. This is to share functionality"""
    def transition(self):
        """Transition to the next setup step"""
        if not self.at_success_state() or self.an_error_occurred():
            self.at_step += 1

            print(
                f"Running step {self.the_states[self.at_step]} ({self.at_step+1}/{len(self.the_states)})"
            )
            self.do_action()

class AbstractDockerState(State):
    name = "DockerState"
    def __init__(self):
        self.at_step = -1
        self.success_state = "neo4j is ready"
        self.error = False
        self.the_states = ["check for docker", "start or run neo4j",
                           "upload data to neo4j", "check upload",
                           self.success_state, "stop neo4j"]
        self._state_actions = {
            self.the_states[0] : self._check,
            self.the_states[1] : self._start_or_run_neo4j,
            self.the_states[2] : self._upload_data_to_neo4j,
            self.the_states[3] : self._check_neo4j_db,
            self.the_states[4] : self._shutdown_neo4j_db
        }
    def at_success_state(self):
        return self.the_states[self.at_step] == self.success_state

    def an_error_occurred(self):
        return self.error

    def do_action(self, a_state=None):
        self.error = True

        if a_state:
            self.at_step = self.the_states.index(a_state)

        do_this_action = self._state_actions.get(
            self.the_states[self.at_step],
            lambda: True
        )
        with_objects_to_check = do_this_action()
        if self.evidence_of_success(with_objects_to_check):
            self.error = False

    @staticmethod
    def evidence_of_success(self, **kwargs):
        return all(kwargs.values())

    @staticmethod
    def _check():
        raise NotImplementedError

    @staticmethod
    def _start_or_run_neo4j():
        raise NotImplementedError

    @staticmethod
    def _upload_data_to_neo4j():
        raise NotImplementedError

    @staticmethod
    def _check_neo4j_db():
        raise NotImplementedError

    @staticmethod
    def _shutdown_neo4j_db():
        raise NotImplementedError