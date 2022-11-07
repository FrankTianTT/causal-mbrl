from typing import Optional

from omegaconf import DictConfig

from cmrl.models.fake_env import VecFakeEnv
from cmrl.algorithms.base_algorithm import BaseAlgorithm, load_offline_data


class OfflineDyna(BaseAlgorithm):
    def __init__(
        self,
        cfg: DictConfig,
        work_dir: Optional[str] = None,
    ):
        super(OfflineDyna, self).__init__(cfg, work_dir)

    def _setup_learn(self):
        load_offline_data(self.env, self.real_replay_buffer, self.cfg.task.dataset, self.cfg.task.use_ratio)

        self.dynamics.learn(
            real_replay_buffer=self.real_replay_buffer,
            longest_epoch=self.cfg.task.longest_epoch,
            improvement_threshold=self.cfg.task.improvement_threshold,
            patience=self.cfg.task.patience,
            work_dir=self.work_dir,
        )
