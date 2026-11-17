from common.demo import strategies
from common import Registry
from agent.model.domain import InputModality
from common.demo.strategies.base_token_count_strategy import BaseTokenCountStrategy

registry = Registry[
            InputModality, BaseTokenCountStrategy
        ](
            base_class=BaseTokenCountStrategy,
            package=strategies,
            key_getter=lambda cls: cls.modality
        )

a = registry.get(InputModality.TEXT)
print(a)