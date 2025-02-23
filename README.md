# About
**kube_little_helper** is a small python tool that leverages LLMs to debug problems in Kubernetes pods

# Requirements
* You need a working installation of [Ollama](https://ollama.com). Then pull the LLM you want to use via the command **ollama pull model_name**. The default LLM used by the tool is **llama3**
* A configured kubernetes environments. The tool will let you choose the kube-context you want to use

# How it works
The tool analyzes the pods in the specified namespace or in all the available namespaces as default behaviour. Then this happens:
* If a pod is in **Running** state and one or more of its containers got restarted then it tries to fetch its logs and send them to the selected LLM for debugging
* For any other state different from **Succeeded** that state of the pod is simply printed

# Things to know and limitations
[Temperature](https://www.promptingguide.ai/introduction/settings) can be tuned to set the determinism of the model. Set it to **0.0** for maximum reproducibility and determinism.
Selecting the right model for your environment is a trial and error process. **Llama3** seems to be generic enough to perform well in most of the environments. 
By using Ollama and a locally running model you are sure confidential data are not sent to any thirdy parties LLM provider (logs of a crashing pods could contain sensitive data you don't want to leak).

This is a weekend project. Be careful at using it for read **production debugging!**
