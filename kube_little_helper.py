import argparse
import sys

from kubernetes import client, config
from kubernetes.client import configuration
from ollama import ChatResponse, chat
from pick import pick


def debug_via_llm(
    container_name: str, logs: str, model_name: str, temperature: float
) -> str:
    print(
        f"Asking an LLM (model:{model_name}, temperature: {temperature}). Analyzing the logs of the container:{container_name}"
    )
    response: ChatResponse = chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": f"You are an expert engineer. Please explain me the following error: {logs}",
            },
        ],
        options={"temperature": temperature},
    )
    return response["message"]["content"]


def analyze_pods(namespace: str, model_name: str, temperature: float) -> None:
    v1 = client.CoreV1Api()
    pods = []
    if namespace:
        print(f"[*] Analysing the pods in the namespace:{namespace}")
        pods = v1.list_namespaced_pod(namespace, watch=False)
    else:
        print("[*] Analysing the pods in all the available namespaces")
        pods = v1.list_pod_for_all_namespaces(watch=False)

    for pod in pods.items:
        if pod.status.phase.lower() == "running":
            print(
                f"==> Starting the analysis of the pod {pod.metadata.name} in the namespace:{pod.metadata.namespace}"
            )
            for container in pod.status.container_statuses:
                if container.restart_count > 0:
                    print(
                        f"Container:{container.name} from pod:{pod.metadata.name} got restarted several times"
                    )
                    if container.last_state.terminated:
                        print(
                            f"Container:{container.name} got terminated for the reason {container.last_state.terminated.reason}"
                        )
                    if not container.ready:
                        print(f"Container:{container.name} is not in ready state")
                    logs = v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace,
                        container=container.name,
                    )
                    llm_response = debug_via_llm(
                        container.name, logs, model_name, temperature
                    )
                    print(
                        "This is the analysis of the logs of the failing container from the selected LLM:"
                    )
                    print(llm_response)
            print(
                f"==> End of the analysis of the pod:{pod.metadata.name} in the namespace:{pod.metadata.namespace}"
            )
        elif pod.status.phase.lower() != "succeeded":
            print(f"Pod:{pod.metadata.name} is in status {pod.status.phase}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name",
        type=str,
        action="store",
        default="llama3",
        help="Set the LLM model to be used. Default is llama3",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        action="store",
        default=0.0,
        help="Set the LLM temperature [0,1]. Default is 0.0 (maximum determinism)",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        action="store",
        default=None,
        help="Run the analysis only in the specified kubernetes namespace. Default is None so all the namespaces are analyzed",
    )
    args = parser.parse_args()
    contexts, active_context = config.list_kube_config_contexts()
    if not contexts:
        print("Error! Cannot find any context in kube-config file.")
        sys.exit(1)
    contexts = [context["name"] for context in contexts]
    active_index = contexts.index(active_context["name"])
    option, _ = pick(
        contexts,
        title="Pick the kubernetes context to load",
        default_index=active_index,
    )
    config.load_kube_config(context=option)
    analyze_pods(args.namespace, args.model_name, args.temperature)
