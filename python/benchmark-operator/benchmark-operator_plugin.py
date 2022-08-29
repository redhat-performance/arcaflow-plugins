#!/usr/bin/env python3

import sys
import traceback
import typing
import tempfile
import subprocess
import kubernetes
from dataclasses import dataclass, field
from arcaflow_plugin_sdk import plugin, validation


@dataclass
class InputParams:
    """
    This is the data structure for the input parameters of the step defined below.
    """
    #name: typing.Annotated[str, validation.min(1)] = field(metadata={
    #    "name": "Name",
    #    "description": "Enter your name here."
    #})
    kubeconfig: str
    #operator_repo: str = "https://github.com/cloud-bulldozer/benchmark-operator.git"
    #operator_branch: str = "v1.0.1"


@dataclass
class CustomResource:
    customresource: str
    kubeconfig: str


@dataclass
class SuccessOutput:
    """
    This is the output data structure for the success case.
    """
    message: str = field(metadata={"name": "Message", "description": "A friendly greeting message."})


@dataclass
class ErrorOutput:
    """
    This is the output data structure in the error  case.
    """
    error: str = field(metadata={"name": "Error", "description": "An explanation why the execution failed."})


# The following is a decorator (starting with @). We add this in front of our function to define the metadata for our
# step.
@plugin.step(
    id="start",
    name="Start Benchmark Operator",
    description="Deploys the Benchmark Operator",
    outputs={"success": SuccessOutput, "error": ErrorOutput},
)
def start_benchmark_operator(params: InputParams) -> typing.Tuple[str, typing.Union[SuccessOutput, ErrorOutput]]:
    """
    The function  is the implementation for the step. It needs the decorator above to make it into a  step. The type
    hints for the params are required.

    :param params:

    :return: the string identifying which output it is, as well the output structure
    """

    kubeconfig_file = tempfile.mkstemp()

    print("==>> Importing kubeconfig...")
    with open(kubeconfig_file[1], 'w') as file:
        file.write(params.kubeconfig)

#    #debug
#    kubectl_cmd = [
#        "kubectl",
#        "--kubeconfig={}".format(kubeconfig_file[1]),
#        "version",
#        "--short"
#    ]
#
#    try:
#        print(subprocess.check_output(kubectl_cmd, text=True, stderr=subprocess.STDOUT))
#    except subprocess.CalledProcessError as error:
#        return "error", ErrorOutput("{} failed with return code {}:\n{}".format(error.cmd[0], error.returncode, error.output))

    ripsaw_cmd = [
        "make",
        "deploy"
    ]

    print("==>> Starting benchmark-operator...")
    try:
        print(subprocess.check_output(ripsaw_cmd, cwd="benchmark-operator", env={"KUBECONFIG": kubeconfig_file[1]},
            text=True, stderr=subprocess.STDOUT))
    except subprocess.CalledProcessError as error:
        return "error", ErrorOutput("{} failed with return code {}:\n{}".format(error.cmd[0], error.returncode, error.output))

    print("==>> Benchmark Operator Deployment Complete!")
    return "success", SuccessOutput("Benchmark Operator successfully deployed!")


# The following is a decorator (starting with @). We add this in front of our function to define the metadata for our
# step.
@plugin.step(
    id="stop",
    name="Stop Benchmark Operator",
    description="Undeploys the Benchmark Operator",
    outputs={"success": SuccessOutput, "error": ErrorOutput},
)
def stop_benchmark_operator(params: InputParams) -> typing.Tuple[str, typing.Union[SuccessOutput, ErrorOutput]]:

    kubeconfig_file = tempfile.mkstemp()

    print("==>> Importing kubeconfig...")
    with open(kubeconfig_file[1], 'w') as file:
        file.write(params.kubeconfig)

    ripsaw_cmd = [
        "make",
        "undeploy"
    ]

    print("==>> Stopping benchmark-operator...")
    try:
        print(subprocess.check_output(ripsaw_cmd, cwd="benchmark-operator", env={"KUBECONFIG": kubeconfig_file[1]},
            text=True, stderr=subprocess.STDOUT))
    except subprocess.CalledProcessError as error:
        return "error", ErrorOutput("{} failed with return code {}:\n{}".format(error.cmd[0], error.returncode, error.output))

    print("==>> Benchmark Operator Stopped!")
    return "success", SuccessOutput("Benchmark Operator successfully removed!")


# The following is a decorator (starting with @). We add this in front of our function to define the metadata for our
# step.
@plugin.step(
    id="cr",
    name="Deploy a CR File",
    description="Passes a CR file to the benchmark-operator to start a benchmark",
    outputs={"success": SuccessOutput, "error": ErrorOutput},
)
def deploy_cr(params: CustomResource) -> typing.Tuple[str, typing.Union[SuccessOutput, ErrorOutput]]:

    kubeconfig_file = tempfile.mkstemp()

    print("==>> Importing kubeconfig...")
    with open(kubeconfig_file[1], 'w') as file:
        file.write(params.kubeconfig)

    cr_file = tempfile.mkstemp()

    print("==>> Importing CR...")
    with open(cr_file[1], 'w') as file:
        file.write(params.customresource)

    ripsaw_cmd = [
        "kubectl",
        "apply",
        "-f",
        cr_file[1]
    ]

    print("==>> Starting benchmark...")
    try:
        print(subprocess.check_output(ripsaw_cmd, cwd="/", env={"KUBECONFIG": kubeconfig_file[1]},
            text=True, stderr=subprocess.STDOUT))
    except subprocess.CalledProcessError as error:
        return "error", ErrorOutput("{} failed with return code {}:\n{}".format(error.cmd[0], error.returncode, error.output))

    print("==>> Benchmark Run Complete!")
    return "success", SuccessOutput("Benchmark successfully run!")


if __name__ == "__main__":
    sys.exit(plugin.run(plugin.build_schema(
        # List your step functions here:
        start_benchmark_operator,
        stop_benchmark_operator,
        deploy_cr
    )))
