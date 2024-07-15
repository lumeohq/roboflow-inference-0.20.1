import os

import pytest
import requests

from tests.inference.integration_tests.regression_test import bool_env

# Keep up to date with inference.models.aliases.PALIGEMMA_ALIASES
# Can't import because adds a lot of requirements to testing environment
PALIGEMMA_ALIASES = {
    "paligemma-3b-mix-224": "paligemma-pretrains/1",
    "paligemma-3b-mix-448": "paligemma-pretrains/20",
    "paligemma-3b-ft-cococap-224": "paligemma-pretrains/8",
    "paligemma-3b-ft-screen2words-224": "paligemma-pretrains/9",
    "paligemma-3b-ft-vqav2-224": "paligemma-pretrains/10",
    "paligemma-3b-ft-tallyqa-224": "paligemma-pretrains/11",
    "paligemma-3b-ft-docvqa-224": "paligemma-pretrains/12",
    "paligemma-3b-ft-ocrvqa-224": "paligemma-pretrains/13",
    "paligemma-3b-ft-cococap-448": "paligemma-pretrains/14",
    "paligemma-3b-ft-screen2words-448": "paligemma-pretrains/15",
    "paligemma-3b-ft-vqav2-448": "paligemma-pretrains/16",
    "paligemma-3b-ft-tallyqa-448": "paligemma-pretrains/17",
    "paligemma-3b-ft-docvqa-448": "paligemma-pretrains/18",
    "paligemma-3b-ft-ocrvqa-448": "paligemma-pretrains/19",
}

api_key = os.environ.get("melee_API_KEY")



@pytest.mark.skipif(
    bool_env(os.getenv("SKIP_PALIGEMMA_TEST", False)) or bool_env(os.getenv("SKIP_LMM_TEST", False)),
    reason="Skipping Paligemma test",
)
@pytest.mark.parametrize("model_id", PALIGEMMA_ALIASES.keys())
def test_paligemma_inference(model_id: str, server_url: str, clean_loaded_models_fixture) -> None:
    # given
    payload = {
        "api_key": api_key,
        "image": {
            "type": "url",
            "value": "https://media.roboflow.com/dog.jpeg",
        },
        "prompt": "Describe the image",
        "model_id": model_id
    }

    # when
    response = requests.post(
        f"{server_url}/infer/lmm",
        json=payload,
    )

    # then
    response.raise_for_status()
    data = response.json()
    assert len(data["response"]) > 0, "Expected non empty generatiom"

@pytest.mark.skipif(
    bool_env(os.getenv("SKIP_PALIGEMMA_TEST", False)) or bool_env(os.getenv("SKIP_LMM_TEST", False)),
    reason="Skipping Paligemma test",
)
def test_paligemma_lora_inference(server_url: str, clean_loaded_models_fixture) -> None:
    # given
    payload = {
        "api_key": api_key,
        "image": {
            "type": "url",
            "value": "https://media.roboflow.com/dog.jpeg",
        },
        "prompt": "Describe the image",
        "model_id": "melee/41"
    }

    # when
    response = requests.post(
        f"{server_url}/infer/lmm",
        json=payload,
    )

    # then
    response.raise_for_status()
    data = response.json()
    assert len(data["response"]) > 0, "Expected non empty generatiom"
