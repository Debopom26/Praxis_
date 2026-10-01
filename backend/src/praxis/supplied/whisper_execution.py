"""Reuse the identical encoder output for language detection and decoding."""
from functools import wraps

import torch


def reuse_encoder(pipeline):
    model = pipeline.model
    original = model.generate

    @wraps(original)
    def generate(*args, **kwargs):
        features = kwargs.get("input_features")
        # Preserve the original path for long-form, timestamps and other callers.
        if (args or features is None or kwargs.get("encoder_outputs") is not None
                or features.shape[-1] != model.config.max_source_positions * 2
                or kwargs.get("return_token_timestamps") or kwargs.get("return_timestamps")
                or kwargs.get("return_segments")
                or features.shape[0] != 1):
            return original(*args, **kwargs)
        with torch.inference_mode():
            encoded = model.get_encoder()(features, return_dict=True)
            kwargs = dict(kwargs)
            del kwargs["input_features"]
            kwargs["encoder_outputs"] = encoded
            return original(**kwargs)

    model.generate = generate
    return original
