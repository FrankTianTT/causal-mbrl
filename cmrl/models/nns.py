import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import pathlib
from typing import Dict, Optional, Sequence, Tuple, Union
from cmrl.models.layers import EnsembleLinearLayer
import cmrl.models.util as models_util
import hydra


class EnsembleMLP(nn.Module):
    _MODEL_FILENAME = "ensemble_mlp.pth"
    _MODEL_SAVE_ATTRS = ["elite_members", "state_dict"]

    def __init__(self,
                 ensemble_num: int = 7,
                 elite_num: int = 5,
                 device: Union[str, torch.device] = "cpu", ):
        super(EnsembleMLP, self).__init__()
        self.ensemble_num = ensemble_num
        self.elite_num = elite_num
        self.device = device

        self.elite_members: Optional[Sequence[int]] = np.random.permutation(ensemble_num)[:elite_num]

    def set_elite(self, elite_indices: Sequence[int]):
        if len(elite_indices) != self.ensemble_num:
            assert len(elite_indices) == self.elite_num
            self.elite_members = list(elite_indices)

    def get_random_index(self, batch_size):
        return np.random.choice(self.elite_members, size=batch_size)

    def save(self, save_dir: Union[str, pathlib.Path]):
        """Saves the model to the given directory."""
        model_dict = {}
        for attr in self._MODEL_SAVE_ATTRS:
            if attr == "state_dict":
                model_dict["state_dict"] = self.state_dict()
            else:
                model_dict[attr] = getattr(self, attr)
        torch.save(model_dict, pathlib.Path(save_dir) / self._MODEL_FILENAME)

    def load(self, load_dir: Union[str, pathlib.Path]):
        """Loads the model from the given path."""
        model_dict = torch.load(pathlib.Path(load_dir) / self._MODEL_FILENAME)
        for attr in model_dict:
            if attr == "state_dict":
                self.load_state_dict(model_dict["state_dict"])
            else:
                setattr(self, attr, model_dict[attr])

    def create_linear_layer(self, l_in, l_out):
        return EnsembleLinearLayer(l_in, l_out,
                                   ensemble_num=self.ensemble_num)

    def get_mse_loss(self,
                     model_in: Dict[(str, torch.Tensor)],
                     target: torch.Tensor) -> torch.Tensor:
        pred_mean, pred_logvar = self.forward(**model_in)
        return F.mse_loss(pred_mean, target, reduction="none")

    def get_nll_loss(self, model_in: Dict[(str, torch.Tensor)],
                     target: torch.Tensor) -> torch.Tensor:
        pred_mean, pred_logvar = self.forward(**model_in)
        nll_loss = models_util.gaussian_nll(pred_mean, pred_logvar, target, reduce=False)
        nll_loss += 0.01 * (self.max_logvar.sum() - self.min_logvar.sum())
        return nll_loss

    def add_save_attr(self,
                      attr: str):
        assert hasattr(self, attr), "Class must has attribute {}".format(attr)
        assert attr not in self._MODEL_SAVE_ATTRS, "Attribute {} has been in model-save-list".format(attr)
        self._MODEL_SAVE_ATTRS.append(attr)

    @property
    def model_file_name(self):
        return self._MODEL_FILENAME