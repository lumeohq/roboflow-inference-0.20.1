from unittest import mock
from unittest.mock import MagicMock

import numpy as np
import pytest

from inference.core.env import WORKFLOWS_MAX_CONCURRENT_STEPS
from inference.core.managers.base import ModelManager
from inference.core.workflows.execution_engine.core import ExecutionEngine
from inference.core.workflows.execution_engine.introspection import blocks_loader

AB_TEST_WORKFLOW = {
    "version": "1.0",
    "inputs": [{"type": "WorkflowImage", "name": "image"}],
    "steps": [
        {
            "type": "ABTest",
            "name": "ab_test",
            "a_step": "$steps.a",
            "b_step": "$steps.b",
        },
        {
            "type": "ObjectDetectionModel",
            "name": "a",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
        },
        {
            "type": "ObjectDetectionModel",
            "name": "b",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "predictions_a",
            "selector": "$steps.a.predictions",
        },
        {
            "type": "JsonField",
            "name": "predictions_b",
            "selector": "$steps.b.predictions",
        },
    ],
}


@pytest.mark.asyncio
@mock.patch.object(blocks_loader, "get_plugin_modules")
async def test_flow_control_step_not_operating_on_batches(
    get_plugin_modules_mock: MagicMock,
    model_manager: ModelManager,
    crowd_image: np.ndarray,
) -> None:
    """
    In this test scenario, we run step (ABTest) which is not running in
    SIMD mode, as it only accepts non-batch parameters - hence
    single decision made at start will affect all downstream execution
    paths.

    We expect, based on flip of coin to execute either step "a" or step "b".

    What is verified from EE standpoint:
    * Creating execution branches for all batch elements, when input batch size is 1
    """
    # given
    get_plugin_modules_mock.return_value = [
        "tests.workflows.integration_tests.execution.stub_plugins.flow_control_plugin"
    ]
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }
    execution_engine = ExecutionEngine.init(
        workflow_definition=AB_TEST_WORKFLOW,
        init_parameters=workflow_init_parameters,
        max_concurrent_steps=WORKFLOWS_MAX_CONCURRENT_STEPS,
    )

    # when
    result = await execution_engine.run_async(runtime_parameters={"image": crowd_image})

    # then
    assert isinstance(result, list), "Expected result to be list"
    assert len(result) == 1, "Single image provided, so one output element expected"
    assert set(result[0].keys()) == {
        "predictions_a",
        "predictions_b",
    }, "Expected all declared outputs to be delivered"
    assert (result[0]["predictions_a"] and not result[0]["predictions_b"]) or (
        not result[0]["predictions_a"] and result[0]["predictions_b"]
    ), "Expected only one of the results provided, mutually exclusive based on random choice"


@pytest.mark.asyncio
@mock.patch.object(blocks_loader, "get_plugin_modules")
async def test_flow_control_step_not_operating_on_batches_affecting_batch_of_inputs(
    get_plugin_modules_mock: MagicMock,
    model_manager: ModelManager,
    crowd_image: np.ndarray,
) -> None:
    """
    In this test scenario, we run step (ABTest) which is not running in
    SIMD mode, as it only accepts non-batch parameters - hence
    single decision made at start will affect all downstream execution
    paths.

    We expect, based on flip of coin to execute either step "a" or step "b".

    What is verified from EE standpoint:
    * Creating execution branches for all batch elements, when input batch size is 4
    """
    # given
    get_plugin_modules_mock.return_value = [
        "tests.workflows.integration_tests.execution.stub_plugins.flow_control_plugin"
    ]
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }
    execution_engine = ExecutionEngine.init(
        workflow_definition=AB_TEST_WORKFLOW,
        init_parameters=workflow_init_parameters,
        max_concurrent_steps=WORKFLOWS_MAX_CONCURRENT_STEPS,
    )

    # when
    result = await execution_engine.run_async(
        runtime_parameters={"image": [crowd_image] * 4}
    )

    # then
    assert isinstance(result, list), "Expected result to be list"
    assert len(result) == 4, "4 images provided, so 4 output elements expected"
    empty_element = (
        "predictions_a" if not result[0]["predictions_a"] else "predictions_b"
    )
    for i in range(4):
        assert set(result[i].keys()) == {
            "predictions_a",
            "predictions_b",
        }, "Expected all declared outputs to be delivered"
        assert (result[i]["predictions_a"] and not result[i]["predictions_b"]) or (
            not result[i]["predictions_a"] and result[i]["predictions_b"]
        ), "Expected only one of the results provided, mutually exclusive based on random choice"
        assert not result[i][
            empty_element
        ], f"Expected `{empty_element}` to be empty for each output, as ABTest takes only non-batch parameters and should decide once for all batch elements"


FILTERING_OPERATION = {
    "type": "DetectionsFilter",
    "filter_operation": {
        "type": "StatementGroup",
        "operator": "and",
        "statements": [
            {
                "type": "BinaryStatement",
                "left_operand": {
                    "type": "DynamicOperand",
                    "operations": [
                        {
                            "type": "ExtractDetectionProperty",
                            "property_name": "class_name",
                        }
                    ],
                },
                "comparator": {"type": "in (Sequence)"},
                "right_operand": {
                    "type": "DynamicOperand",
                    "operand_name": "classes",
                },
            },
            {
                "type": "BinaryStatement",
                "left_operand": {
                    "type": "DynamicOperand",
                    "operations": [
                        {
                            "type": "ExtractDetectionProperty",
                            "property_name": "size",
                        },
                    ],
                },
                "comparator": {"type": "(Number) >="},
                "right_operand": {
                    "type": "DynamicOperand",
                    "operand_name": "image",
                    "operations": [
                        {
                            "type": "ExtractImageProperty",
                            "property_name": "size",
                        },
                        {"type": "Multiply", "other": 0.02},
                    ],
                },
            },
        ],
    },
}

WORKFLOW_WITH_CONDITION_DEPENDENT_ON_MODEL_PREDICTION = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
        {"type": "WorkflowParameter", "name": "classes"},
        {"type": "WorkflowParameter", "name": "detections_meeting_condition"},
    ],
    "steps": [
        {
            "type": "ObjectDetectionModel",
            "name": "a",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
        },
        {
            "type": "Condition",
            "name": "condition",
            "condition_statement": {
                "type": "StatementGroup",
                "statements": [
                    {
                        "type": "BinaryStatement",
                        "left_operand": {
                            "type": "DynamicOperand",
                            "operand_name": "prediction",
                            "operations": [
                                FILTERING_OPERATION,
                                {"type": "SequenceLength"},
                            ],
                        },
                        "comparator": {"type": "(Number) >="},
                        "right_operand": {
                            "type": "DynamicOperand",
                            "operand_name": "detections_meeting_condition",
                        },
                    }
                ],
            },
            "evaluation_parameters": {
                "image": "$inputs.image",
                "prediction": "$steps.a.predictions",
                "classes": "$inputs.classes",
                "detections_meeting_condition": "$inputs.detections_meeting_condition",
            },
            "steps_if_true": ["$steps.b"],
            "steps_if_false": ["$steps.c"],
        },
        {
            "type": "ObjectDetectionModel",
            "name": "b",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
        },
        {
            "type": "ObjectDetectionModel",
            "name": "c",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "predictions_b",
            "selector": "$steps.b.predictions",
        },
        {
            "type": "JsonField",
            "name": "predictions_c",
            "selector": "$steps.c.predictions",
        },
    ],
}


@pytest.mark.asyncio
async def test_flow_control_step_affecting_batches(
    model_manager: ModelManager,
    crowd_image: np.ndarray,
    dogs_image: np.ndarray,
) -> None:
    """
    Inn this test scenario, we make predictions from object detection model.
    Then we make if-else statement for each image form input batch checking if
    model found at least 2 big instances of classes {car, person}. If that is
    the case we run $steps.b otherwise $steps.c.

    What is verified from EE standpoint:
    * Creating execution branches for each batch element separately, and then
    executing downstream step according to decision made at previous step -
    with execution branches being independent
    * proper behavior of steps expecting non-empty inputs w.r.t. masks for
    execution branches
    * proper broadcasting of non-batch parameters for execution branches
    """
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }
    execution_engine = ExecutionEngine.init(
        workflow_definition=WORKFLOW_WITH_CONDITION_DEPENDENT_ON_MODEL_PREDICTION,
        init_parameters=workflow_init_parameters,
        max_concurrent_steps=WORKFLOWS_MAX_CONCURRENT_STEPS,
    )

    # when
    result = await execution_engine.run_async(
        runtime_parameters={
            "image": [crowd_image, dogs_image],
            "classes": ["person", "car"],
            "detections_meeting_condition": 2,
        }
    )

    # then
    assert isinstance(result, list), "Expected result to be list"
    assert len(result) == 2, "2 images provided, so 2 output elements expected"
    assert result[0].keys() == {
        "predictions_b",
        "predictions_c",
    }, "Expected all declared outputs to be delivered for first result"
    assert result[1].keys() == {
        "predictions_b",
        "predictions_c",
    }, "Expected all declared outputs to be delivered for second result"
    assert (
        result[0]["predictions_b"] and not result[0]["predictions_c"]
    ), "At crowd image it is expected to spot 2 big instances of classes person, car - hence model b should fire"
    assert (
        not result[1]["predictions_b"] and result[1]["predictions_c"]
    ), "At dogs image it is not expected to spot people nor cars - hence model c should fire"


WORKFLOW_WITH_CONDITION_DEPENDENT_ON_CROPS = {
    "version": "1.0",
    "inputs": [{"type": "WorkflowImage", "name": "image"}],
    "steps": [
        {
            "type": "ObjectDetectionModel",
            "name": "first_detection",
            "image": "$inputs.image",
            "model_id": "yolov8n-640",
        },
        {
            "type": "DetectionsTransformation",
            "name": "enlarging_boxes",
            "predictions": "$steps.first_detection.predictions",
            "operations": [
                {"type": "DetectionsOffset", "offset_x": 50, "offset_y": 50}
            ],
        },
        {
            "type": "Crop",
            "name": "first_crop",
            "image": "$inputs.image",
            "predictions": "$steps.enlarging_boxes.predictions",
        },
        {
            "type": "ObjectDetectionModel",
            "name": "second_detection",
            "image": "$steps.first_crop.crops",
            "model_id": "yolov8n-640",
            "class_filter": ["dog"],
        },
        {
            "type": "ContinueIf",
            "name": "continue_if",
            "condition_statement": {
                "type": "StatementGroup",
                "statements": [
                    {
                        "type": "BinaryStatement",
                        "left_operand": {
                            "type": "DynamicOperand",
                            "operand_name": "prediction",
                            "operations": [{"type": "SequenceLength"}],
                        },
                        "comparator": {"type": "(Number) =="},
                        "right_operand": {
                            "type": "StaticOperand",
                            "value": 1,
                        },
                    }
                ],
            },
            "evaluation_parameters": {
                "prediction": "$steps.second_detection.predictions"
            },
            "next_steps": ["$steps.classification"],
        },
        {
            "type": "ClassificationModel",
            "name": "classification",
            "image": "$steps.first_crop.crops",
            "model_id": "dog-breed-xpaq6/1",
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "dog_classification",
            "selector": "$steps.classification.predictions",
        }
    ],
}


@pytest.mark.asyncio
async def test_flow_control_step_affecting_data_with_increased_dimensionality(
    model_manager: ModelManager,
    crowd_image: np.ndarray,
    dogs_image: np.ndarray,
) -> None:
    """
    In this test scenario we verify if we can successfully apply conditional
    branching when data dimensionality increases.
    We first make detections on input images and perform crop increasing
    dimensionality to 2. Then we make another detections on cropped images
    and check if inside crop we only see one instance of class dog (very naive
    way of making sure that bboxes contain only single objects).
    Only if that condition is true, we run classification model - to
    classify dog breed.

    What is verified from EE standpoint:
    * Creating execution branches for each batch element separately on deeper
    dimensionality levels and then executing downstream step according to
    decision made previously - with execution branches being independent
    * proper behavior of steps expecting non-empty inputs w.r.t. masks for
    execution branches
    * correctness of building nested outputs
    """
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
    }
    execution_engine = ExecutionEngine.init(
        workflow_definition=WORKFLOW_WITH_CONDITION_DEPENDENT_ON_CROPS,
        init_parameters=workflow_init_parameters,
        max_concurrent_steps=WORKFLOWS_MAX_CONCURRENT_STEPS,
    )

    # when
    result = await execution_engine.run_async(
        runtime_parameters={
            "image": [crowd_image, dogs_image],
        }
    )

    # then
    assert isinstance(result, list), "Expected result to be list"
    assert len(result) == 2, "2 images provided, so 2 output elements expected"
    assert result[0].keys() == {
        "dog_classification"
    }, "Expected all declared outputs to be delivered for first result"
    assert result[0].keys() == {
        "dog_classification"
    }, "Expected all declared outputs to be delivered for second result"
    assert (
        result[0]["dog_classification"] == [None] * 12
    ), "There is 12 crops for first image, but none got dogs classification results due to not meeting condition"
    assert (
        len([e for e in result[1]["dog_classification"] if e]) == 2
    ), "Expected 2 bboxes of dogs detected"
