import pytest

from inference.core.managers.base import ModelManager
from inference.core.workflows.errors import (
    ExecutionGraphStructureError,
    InvalidReferenceTargetError,
)
from inference.core.workflows.execution_engine.compiler.core import compile_workflow

WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_IMAGE_IN_STEP = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
    ],
    "steps": [
        {
            "type": "RoboflowObjectDetectionModel",
            "name": "detection",
            "image": "$inputs.non_existing",
            "model_id": "yolov8n-640",
            "class_filter": ["car"],
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "predictions",
            "selector": "$steps.detection.*",
        },
    ],
}


@pytest.mark.asyncio
async def test_compilation_of_workflow_with_reference_to_non_existing_image_in_step(
    model_manager: ModelManager,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }

    # when
    with pytest.raises(InvalidReferenceTargetError) as error:
        _ = compile_workflow(
            workflow_definition=WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_IMAGE_IN_STEP,
            init_parameters=workflow_init_parameters,
        )

    # then
    assert "$inputs.non_existing" in str(error.value)


WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_IMAGE_IN_OUTPUT = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
    ],
    "steps": [
        {
            "type": "RoboflowObjectDetectionModel",
            "name": "detection",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
            "class_filter": ["car"],
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "image",
            "selector": "$inputs.non_existing",
        },
    ],
}


@pytest.mark.asyncio
async def test_compilation_of_workflow_with_reference_to_non_existing_image_in_output(
    model_manager: ModelManager,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }

    # when
    with pytest.raises(InvalidReferenceTargetError) as error:
        _ = compile_workflow(
            workflow_definition=WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_IMAGE_IN_OUTPUT,
            init_parameters=workflow_init_parameters,
        )

    # then
    assert "$inputs.non_existing" in str(error.value)


WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_STEP_OUTPUT_IN_STEP = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
    ],
    "steps": [
        {
            "type": "RoboflowObjectDetectionModel",
            "name": "detection",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
            "class_filter": ["car"],
        },
        {
            "type": "Crop",
            "name": "crops",
            "image": "$steps.not_existing.crops",
            "predictions": "$steps.detection.predictions",
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "crops",
            "selector": "$steps.crops.*",
        },
    ],
}


@pytest.mark.asyncio
async def test_compilation_of_workflow_with_reference_to_non_existing_step_output_in_step(
    model_manager: ModelManager,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }

    # when
    with pytest.raises(InvalidReferenceTargetError) as error:
        _ = compile_workflow(
            workflow_definition=WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_STEP_OUTPUT_IN_STEP,
            init_parameters=workflow_init_parameters,
        )

    # then
    assert "$steps.not_existing" in str(error.value)


WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_STEP_IN_OUTPUT = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
    ],
    "steps": [
        {
            "type": "RoboflowObjectDetectionModel",
            "name": "detection",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
            "class_filter": ["car"],
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "image",
            "selector": "$steps.non_existing.*",
        },
    ],
}


@pytest.mark.asyncio
async def test_compilation_of_workflow_with_reference_to_non_existing_step_in_output(
    model_manager: ModelManager,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }

    # when
    with pytest.raises(InvalidReferenceTargetError) as error:
        _ = compile_workflow(
            workflow_definition=WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_STEP_IN_OUTPUT,
            init_parameters=workflow_init_parameters,
        )

    # then
    assert "$steps.non_existing" in str(error.value)


WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_STEP_OUTPUT_OF_EXISTING_STEP = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
    ],
    "steps": [
        {
            "type": "RoboflowObjectDetectionModel",
            "name": "detection",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
            "class_filter": ["car"],
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "image",
            "selector": "$steps.detection.dummy",
        },
    ],
}


@pytest.mark.asyncio
async def test_compilation_of_workflow_with_reference_to_non_existing_step_output_of_existing_step(
    model_manager: ModelManager,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }

    # when
    with pytest.raises(InvalidReferenceTargetError) as error:
        _ = compile_workflow(
            workflow_definition=WORKFLOW_WITH_REFERENCE_TO_NON_EXISTING_STEP_OUTPUT_OF_EXISTING_STEP,
            init_parameters=workflow_init_parameters,
        )

    # then
    assert "$steps.detection.dummy" in str(error.value)
