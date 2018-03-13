import luigi


class RerunnableTask(luigi.Task):
    """ Instance of luigi task that allows for re-running """

    def complete(self):
        """ If force-rerun has been passed, always return False so the task will be run """
        if self.FORCE_RERUN:
            return False

        complete_status = super(RerunnableTask, self).complete()
        return complete_status
