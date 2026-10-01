from types import SimpleNamespace

import torch
from praxis.supplied.whisper_execution import reuse_encoder


def test_encoder_reused_without_changing_generation_options():
    encoded = object()
    seen = []
    def generate(*args, **kwargs):
        seen.append((args, kwargs))
        return "result"
    model = SimpleNamespace(generate=generate, config=SimpleNamespace(max_source_positions=1500),
                            get_encoder=lambda: lambda *args, **kwargs: encoded)
    pipeline = SimpleNamespace(model=model)
    original = reuse_encoder(pipeline)
    assert original is generate
    assert model.generate(input_features=torch.zeros(1, 80, 3000), language=None, use_cache=True) == "result"
    assert seen[-1][1] == {"encoder_outputs": encoded, "language": None, "use_cache": True}
    # Unsupported forms keep the library's original behavior.
    for size in (100, 6000):
        features = torch.zeros(1, 80, size)
        model.generate(input_features=features)
        assert seen[-1][1]["input_features"] is features
    features = torch.zeros(1, 80, 3000)
    model.generate(input_features=features, return_token_timestamps=True)
    assert seen[-1][1]["input_features"] is features
