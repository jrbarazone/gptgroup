
from __future__ import annotations
import json

from autogpts.autogpt.autogpt.core.configuration import AFAASModel
from autogpts.autogpt.autogpt.core.agents import AbstractAgent   


from  autogpts.AFAAS.app.sdk.forge_log import ForgeLogger
LOG = ForgeLogger(name=__name__)


from typing import TYPE_CHECKING
from pydantic import Field


from .base import BaseTask
from .plan import Plan

class TaskStack(AFAASModel):
    parent_task : BaseTask = Field(..., exclude=True)
    _task_ids : list[str] = [] 

    def dict(self, *args, **kwargs) -> dict:
        return {"task_ids": self._task_ids}
    
    def json(self, *args, **kwargs):
        return json.dumps(self.dict())
         
    def __len__(self):
        return len(self._task_ids)

    def __iter__(self):
        return iter(self._task_ids)

    def add(self, task: BaseTask):
        LOG.trace(f"Adding task ``{LOG.italic(task.task_goal)}`` to stack")
        """
        Add a task. Can also mark it as ready.
        """
        self._task_ids.append(task.task_id)
        if isinstance(self.parent_task, Plan):
            plan: Plan = self.parent_task
        else:
            plan: Plan = self.parent_task.agent.plan
            plan._register_task_as_modified(task_id=self.parent_task.task_id)

        if(self.parent_task.subtasks == self) : 
            # FIXME: Evaluate what is the best way to evaluate predecessors
            LOG.info(f"Added task ``{LOG.italic(task.task_goal)}`` as subtask of task ``{LOG.italic(self.parent_task.task_goal)}``")
            LOG.debug((f"As is subtask do not inherit from parent predecessors, 3 options are considered :\n"
                        + f"- Always add all predecessors of parent task to subtask predecessors\n"
                        + f"- Smartly/Dynamicaly add all predecessors of parent task to subtask predecessors\n"
                        + f"- Consider parent predecessor when evaluatin `Task.is_ready()`\n"))
            LOG.debug(f"Added subtask should only be added if parent_task is READY")
            

    def get_task(self, task_id) -> BaseTask:
        """
        Get a specific task.
        """
        return self.parent_task.agent.plan.get_task(task_id)

    def get_all_tasks(self)-> list[BaseTask]:
        """
        Get all tasks. If only_ready is True, return only ready tasks.
        """
        return [self.parent_task.agent.plan.get_task(task_id) for task_id in self._task_ids]

    def get_ready_tasks(self)-> list[BaseTask]:
        """
        Get all ready tasks.
        """
        ready_task_ids_set = set(self.parent_task.agent.plan.get_ready_tasks())

        common_task_ids = ready_task_ids_set.intersection(self._task_ids)

        return [self.parent_task.agent.plan.get_task(task_id) for task_id in common_task_ids]
    
    def get_active_tasks(self)-> list[BaseTask]:
        """
        Get all active tasks.
        """
        active_task_ids_set = set(self.parent_task.agent.plan.get_active_tasks())

        common_task_ids = active_task_ids_set.intersection(self._task_ids)

        return [self.parent_task.agent.plan.get_task(task_id) for task_id in common_task_ids]


# Additional methods can be added as needed
TaskStack.update_forward_refs()