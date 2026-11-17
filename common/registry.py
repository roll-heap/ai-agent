from typing import TypeVar, Hashable, Generic, Type, Callable

from common.class_scanner import ClassScanner
from exception import AgentException

K = TypeVar("K", bound=Hashable)
T = TypeVar("T")


class Registry(Generic[K, T]):
    """
    通用注册器
    K：注册键类型
    T:注册对象类型
    """
    def __init__(
        self,
        base_class: Type[T],
        package,
        key_getter: Callable[[Type[T]], K] | None = None,
        instance_factory: Callable[[Type[T]], T] | None = None,
    ):
        self._base_class = base_class
        self._items: dict[K, T]={}
        self._instance_factory = instance_factory or (lambda cls: cls())
        if package:
            if key_getter is None:
                raise ValueError("自动扫描注册时必须提供key_getter")
            classes = ClassScanner.build_registry(
                base_class=base_class,
                package=package,
                key_getter=key_getter
            )
            for key, item_class in classes.items():
                self.register(key=key, item=self._instance_factory(item_class))

    def register(self,key: K, item: T, *, replace: bool=False):
        """注册对象
        *：分隔符，在*之后的参数必须是关键字传参
        """
        if not isinstance(item, self._base_class):
            raise AgentException(f"注册对象必须继承{self._base_class}")
        if key in self._items and not replace:
            raise AgentException(f"重复注册：{key}")
        self._items[key] = item

    def get(self, key: K) -> T:
        """获取注册对象"""
        item = self._items.get(key)
        if item is None:
            raise AgentException(f"未注册对应对象：{key}")
        return item

    def supports(self, key: K) -> bool:
        """判断是否存在指定key"""
        return key in self._items

    def unregister(self, key: K) -> T:
        """注销对象"""
        if key not in self._items:
            raise AgentException(f"未注册对应对象:{key}")
        return self._items.pop(key)

    def clear(self) -> None:
        """清空注册表"""
        self._items.clear()

    @property
    def items(self) -> dict[K, T]:
        """获取注册对象副本"""
        return self._items.copy()

    @property
    def keys(self) -> tuple[K,...]:
        """获取所有注册表"""
        return tuple(self._items.keys())

    def __contains__(self, key: K) -> bool:
        return key in self._items

    def __len__(self) -> int:
        return len(self._items)