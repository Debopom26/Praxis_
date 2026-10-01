
import re
import shutil
import sys
import importlib.util
from pathlib import Path

import torch

from .common import (
    BaseAdapter,
    extract_state,
    load_state_flexible,
    logits_to_evidence
)


class W2V2AASISTAdapter(BaseAdapter):

    name = "w2v2_aasist"


    def _prepare_runtime_model(self):

        repo = Path(
            self.paths["repo"]
        )

        source = repo / "model.py"

        if not source.exists():
            source = (
                repo /
                "Simplified_CM_solution.py"
            )

        if not source.exists():
            raise FileNotFoundError(
                f"W2V2 model implementation not found in {repo}"
            )

        generated = (
            Path(__file__).parent /
            "_w2v2_runtime_model.py"
        )

        text = source.read_text(
            encoding="utf-8"
        )

        xlsr = str(
            Path(
                self.paths["xlsr_checkpoint"]
            )
        )

        # Replace the upstream hard-coded XLS-R checkpoint.
        text, count = re.subn(
            r"cp_path\s*=\s*[\"'][^\"']*xlsr2_300m\.pt[\"']",
            f'cp_path = r"{xlsr}"',
            text,
            count=1
        )

        if count == 0:
            raise RuntimeError(
                "Could not patch XLS-R path in W2V2 model.py"
            )

        # Upstream code forces the SSL frontend back into train()
        # during feature extraction. For deployed inference we keep
        # it deterministic.
        text = text.replace(
            "self.model.train()",
            "self.model.eval()"
        )

        generated.write_text(
            text,
            encoding="utf-8"
        )

        return generated


    def _load(self):

        try:
            import fairseq
        except Exception as e:
            raise RuntimeError(
                "Fairseq is not available in this Python environment. "
                "Run Praxis acoustic runtime from the Python 3.10 "
                "environment used for W2V2 training."
            ) from e

        runtime_model = (
            self._prepare_runtime_model()
        )

        spec = importlib.util.spec_from_file_location(
            "praxis_w2v2_runtime",
            runtime_model
        )

        module = importlib.util.module_from_spec(
            spec
        )

        spec.loader.exec_module(
            module
        )

        # Tak et al. implementation:
        # Model(d_args, device)
        try:
            self.model = module.Model(
                None,
                self.device
            )

        except Exception:
            import argparse

            self.model = module.Model(
                argparse.Namespace(),
                self.device
            )

        artifact = torch.load(
            self.paths["checkpoint"],
            map_location="cpu",
            weights_only=False
        )

        state = extract_state(
            artifact,
            [
                "model_state_dict",
                "state_dict"
            ]
        )

        load_state_flexible(
            self.model,
            state
        )

        self.model.to(self.device)
        self.model.eval()


    def _predict(self, audio):

        # Tak W2V2 implementation accepts waveform and internally
        # squeezes the final singleton dimension.
        x = torch.from_numpy(
            audio
        ).unsqueeze(0).unsqueeze(-1)

        x = x.to(
            self.device
        )

        try:
            output = self.model(
                x,
                Freq_aug=False
            )
        except TypeError:
            output = self.model(x)

        if isinstance(output, (tuple, list)):
            logits = output[-1]
        else:
            logits = output

        result = logits_to_evidence(
            logits
        )

        result["model_input_samples"] = 64000

        return result
