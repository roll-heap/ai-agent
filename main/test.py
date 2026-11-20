from transformers import AutoTokenizer

from common.utils import AgentUtils

project_path = AgentUtils.get_project_root(project_name="ai-agent")
cache_dir = project_path / "cache" / "hugging_face_cache"/"deepseek-ai/DeepSeek-R1"
cache_dir.mkdir(parents=True, exist_ok=True)
tokenizer = AutoTokenizer.from_pretrained(
    pretrained_model_name_or_path='deepseek-ai/DeepSeek-R1',
    revision="main",
    cache_dir=cache_dir,
    local_files_only=False #是否使用本地缓存文件
) # type: ignore