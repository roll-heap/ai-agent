
import importlib
import inspect
import pkgutil
from typing import TypeVar, Hashable, Callable, Type

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)

class ClassScanner:
    """
    通用类扫描工具。
    功能：
    1. 自动扫描指定包及其子包
    2. 自动导入模块
    3. 查找指定基类的所有实现类
    4. 排除抽象类
    5. 排除从其他模块导入的类
    6. 自动去重
    不依赖任何具体业务模块。
    """
    @staticmethod
    def scan(base_class: type[T], package, recursive: bool = True) -> list[type[T]]:
        """
        扫描指定包下所有 base_class 的具体实现类。
        Args:
            base_class: 被扫描的基类
            package: Python package 对象
            recursive: 是否递归扫描子包
        Returns:
            发现的具体实现类
        """
        if not inspect.isclass(base_class):
            raise TypeError("base_class 必须是类")
        if not hasattr(package, "__path__"):
            raise TypeError("package 必须是一个 Python 包")
        discovered = {}
        # 扫描包及子包
        if recursive:
            modules = pkgutil.walk_packages(package.__path__, prefix=package.__name__ + ".",)
        else:
            modules = (
                item
                for item in pkgutil.iter_modules(package.__path__, prefix=package.__name__ + ".")
            )
        for module_info in modules:
            module_name = module_info.name
            # 导入模块，触发类定义
            module = importlib.import_module(module_name)
            # 查找模块中定义的类
            for _, cls in inspect.getmembers(
                module,
                inspect.isclass,
            ):
                # 排除基类本身
                if cls is base_class:
                    continue
                # 只接受指定基类的子类
                if not issubclass(cls, base_class):
                    continue
                # 排除抽象类
                if inspect.isabstract(cls):
                    continue
                # 排除从其他模块导入的类
                if cls.__module__ != module.__name__:
                    continue
                # 使用类的完整路径去重
                class_key = (cls.__module__,cls.__qualname__)
                discovered[class_key] = cls
        return list(discovered.values())

    @classmethod
    def build_registry(
            cls,
            base_class: type[T],
            package,
            key_getter: Callable[[Type[T]], K] | None,
            recursive: bool = True
    ) -> dict:
        """
        扫描并构建通用注册表。
        key_getter:
            用于从实现类中提取注册键。
        例如：
            lambda strategy: strategy.modality
        """
        implementations = cls.scan(base_class=base_class, package=package, recursive=recursive,)
        registry = {}
        for implementation in implementations:
            key = key_getter(implementation)
            if key is None:
                raise ValueError(f"{implementation.__name__} 注册键不能为空")
            if key in registry:
                raise ValueError(f"重复注册: {key}, {registry[key].__name__}, {implementation.__name__}")
            registry[key] = implementation
        return registry
