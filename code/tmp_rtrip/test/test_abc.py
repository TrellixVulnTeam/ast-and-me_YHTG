"""Unit tests for abc.py."""
import unittest
from test import support
import abc
from inspect import isabstract


class TestLegacyAPI(unittest.TestCase):

    def test_abstractproperty_basics(self):

        @abc.abstractproperty
        def foo(self):
            pass
        self.assertTrue(foo.__isabstractmethod__)

        def bar(self):
            pass
        self.assertFalse(hasattr(bar, '__isabstractmethod__'))


        class C(metaclass=abc.ABCMeta):

            @abc.abstractproperty
            def foo(self):
                return 3
        self.assertRaises(TypeError, C)


        class D(C):

            @property
            def foo(self):
                return super().foo
        self.assertEqual(D().foo, 3)
        self.assertFalse(getattr(D.foo, '__isabstractmethod__', False))

    def test_abstractclassmethod_basics(self):

        @abc.abstractclassmethod
        def foo(cls):
            pass
        self.assertTrue(foo.__isabstractmethod__)

        @classmethod
        def bar(cls):
            pass
        self.assertFalse(getattr(bar, '__isabstractmethod__', False))


        class C(metaclass=abc.ABCMeta):

            @abc.abstractclassmethod
            def foo(cls):
                return cls.__name__
        self.assertRaises(TypeError, C)


        class D(C):

            @classmethod
            def foo(cls):
                return super().foo()
        self.assertEqual(D.foo(), 'D')
        self.assertEqual(D().foo(), 'D')

    def test_abstractstaticmethod_basics(self):

        @abc.abstractstaticmethod
        def foo():
            pass
        self.assertTrue(foo.__isabstractmethod__)

        @staticmethod
        def bar():
            pass
        self.assertFalse(getattr(bar, '__isabstractmethod__', False))


        class C(metaclass=abc.ABCMeta):

            @abc.abstractstaticmethod
            def foo():
                return 3
        self.assertRaises(TypeError, C)


        class D(C):

            @staticmethod
            def foo():
                return 4
        self.assertEqual(D.foo(), 4)
        self.assertEqual(D().foo(), 4)


class TestABC(unittest.TestCase):

    def test_ABC_helper(self):


        class C(abc.ABC):

            @classmethod
            @abc.abstractmethod
            def foo(cls):
                return cls.__name__
        self.assertEqual(type(C), abc.ABCMeta)
        self.assertRaises(TypeError, C)


        class D(C):

            @classmethod
            def foo(cls):
                return super().foo()
        self.assertEqual(D.foo(), 'D')

    def test_abstractmethod_basics(self):

        @abc.abstractmethod
        def foo(self):
            pass
        self.assertTrue(foo.__isabstractmethod__)

        def bar(self):
            pass
        self.assertFalse(hasattr(bar, '__isabstractmethod__'))

    def test_abstractproperty_basics(self):

        @property
        @abc.abstractmethod
        def foo(self):
            pass
        self.assertTrue(foo.__isabstractmethod__)

        def bar(self):
            pass
        self.assertFalse(getattr(bar, '__isabstractmethod__', False))


        class C(metaclass=abc.ABCMeta):

            @property
            @abc.abstractmethod
            def foo(self):
                return 3
        self.assertRaises(TypeError, C)


        class D(C):

            @C.foo.getter
            def foo(self):
                return super().foo
        self.assertEqual(D().foo, 3)

    def test_abstractclassmethod_basics(self):

        @classmethod
        @abc.abstractmethod
        def foo(cls):
            pass
        self.assertTrue(foo.__isabstractmethod__)

        @classmethod
        def bar(cls):
            pass
        self.assertFalse(getattr(bar, '__isabstractmethod__', False))


        class C(metaclass=abc.ABCMeta):

            @classmethod
            @abc.abstractmethod
            def foo(cls):
                return cls.__name__
        self.assertRaises(TypeError, C)


        class D(C):

            @classmethod
            def foo(cls):
                return super().foo()
        self.assertEqual(D.foo(), 'D')
        self.assertEqual(D().foo(), 'D')

    def test_abstractstaticmethod_basics(self):

        @staticmethod
        @abc.abstractmethod
        def foo():
            pass
        self.assertTrue(foo.__isabstractmethod__)

        @staticmethod
        def bar():
            pass
        self.assertFalse(getattr(bar, '__isabstractmethod__', False))


        class C(metaclass=abc.ABCMeta):

            @staticmethod
            @abc.abstractmethod
            def foo():
                return 3
        self.assertRaises(TypeError, C)


        class D(C):

            @staticmethod
            def foo():
                return 4
        self.assertEqual(D.foo(), 4)
        self.assertEqual(D().foo(), 4)

    def test_abstractmethod_integration(self):
        for abstractthing in [abc.abstractmethod, abc.abstractproperty, abc
            .abstractclassmethod, abc.abstractstaticmethod]:


            class C(metaclass=abc.ABCMeta):

                @abstractthing
                def foo(self):
                    pass

                def bar(self):
                    pass
            self.assertEqual(C.__abstractmethods__, {'foo'})
            self.assertRaises(TypeError, C)
            self.assertTrue(isabstract(C))


            class D(C):

                def bar(self):
                    pass
            self.assertEqual(D.__abstractmethods__, {'foo'})
            self.assertRaises(TypeError, D)
            self.assertTrue(isabstract(D))


            class E(D):

                def foo(self):
                    pass
            self.assertEqual(E.__abstractmethods__, set())
            E()
            self.assertFalse(isabstract(E))


            class F(E):

                @abstractthing
                def bar(self):
                    pass
            self.assertEqual(F.__abstractmethods__, {'bar'})
            self.assertRaises(TypeError, F)
            self.assertTrue(isabstract(F))

    def test_descriptors_with_abstractmethod(self):


        class C(metaclass=abc.ABCMeta):

            @property
            @abc.abstractmethod
            def foo(self):
                return 3

            @foo.setter
            @abc.abstractmethod
            def foo(self, val):
                pass
        self.assertRaises(TypeError, C)


        class D(C):

            @C.foo.getter
            def foo(self):
                return super().foo
        self.assertRaises(TypeError, D)


        class E(D):

            @D.foo.setter
            def foo(self, val):
                pass
        self.assertEqual(E().foo, 3)


        class NotBool(object):

            def __bool__(self):
                raise ValueError()
            __len__ = __bool__
        with self.assertRaises(ValueError):


            class F(C):

                def bar(self):
                    pass
                bar.__isabstractmethod__ = NotBool()
                foo = property(bar)

    def test_customdescriptors_with_abstractmethod(self):


        class Descriptor:

            def __init__(self, fget, fset=None):
                self._fget = fget
                self._fset = fset

            def getter(self, callable):
                return Descriptor(callable, self._fget)

            def setter(self, callable):
                return Descriptor(self._fget, callable)

            @property
            def __isabstractmethod__(self):
                return getattr(self._fget, '__isabstractmethod__', False
                    ) or getattr(self._fset, '__isabstractmethod__', False)


        class C(metaclass=abc.ABCMeta):

            @Descriptor
            @abc.abstractmethod
            def foo(self):
                return 3

            @foo.setter
            @abc.abstractmethod
            def foo(self, val):
                pass
        self.assertRaises(TypeError, C)


        class D(C):

            @C.foo.getter
            def foo(self):
                return super().foo
        self.assertRaises(TypeError, D)


        class E(D):

            @D.foo.setter
            def foo(self, val):
                pass
        self.assertFalse(E.foo.__isabstractmethod__)

    def test_metaclass_abc(self):


        class A(metaclass=abc.ABCMeta):

            @abc.abstractmethod
            def x(self):
                pass
        self.assertEqual(A.__abstractmethods__, {'x'})


        class meta(type, A):

            def x(self):
                return 1


        class C(metaclass=meta):
            pass

    def test_registration_basics(self):


        class A(metaclass=abc.ABCMeta):
            pass


        class B(object):
            pass
        b = B()
        self.assertFalse(issubclass(B, A))
        self.assertFalse(issubclass(B, (A,)))
        self.assertNotIsInstance(b, A)
        self.assertNotIsInstance(b, (A,))
        B1 = A.register(B)
        self.assertTrue(issubclass(B, A))
        self.assertTrue(issubclass(B, (A,)))
        self.assertIsInstance(b, A)
        self.assertIsInstance(b, (A,))
        self.assertIs(B1, B)


        class C(B):
            pass
        c = C()
        self.assertTrue(issubclass(C, A))
        self.assertTrue(issubclass(C, (A,)))
        self.assertIsInstance(c, A)
        self.assertIsInstance(c, (A,))

    def test_register_as_class_deco(self):


        class A(metaclass=abc.ABCMeta):
            pass


        @A.register
        class B(object):
            pass
        b = B()
        self.assertTrue(issubclass(B, A))
        self.assertTrue(issubclass(B, (A,)))
        self.assertIsInstance(b, A)
        self.assertIsInstance(b, (A,))


        @A.register
        class C(B):
            pass
        c = C()
        self.assertTrue(issubclass(C, A))
        self.assertTrue(issubclass(C, (A,)))
        self.assertIsInstance(c, A)
        self.assertIsInstance(c, (A,))
        self.assertIs(C, A.register(C))

    def test_isinstance_invalidation(self):


        class A(metaclass=abc.ABCMeta):
            pass


        class B:
            pass
        b = B()
        self.assertFalse(isinstance(b, A))
        self.assertFalse(isinstance(b, (A,)))
        token_old = abc.get_cache_token()
        A.register(B)
        token_new = abc.get_cache_token()
        self.assertNotEqual(token_old, token_new)
        self.assertTrue(isinstance(b, A))
        self.assertTrue(isinstance(b, (A,)))

    def test_registration_builtins(self):


        class A(metaclass=abc.ABCMeta):
            pass
        A.register(int)
        self.assertIsInstance(42, A)
        self.assertIsInstance(42, (A,))
        self.assertTrue(issubclass(int, A))
        self.assertTrue(issubclass(int, (A,)))


        class B(A):
            pass
        B.register(str)


        class C(str):
            pass
        self.assertIsInstance('', A)
        self.assertIsInstance('', (A,))
        self.assertTrue(issubclass(str, A))
        self.assertTrue(issubclass(str, (A,)))
        self.assertTrue(issubclass(C, A))
        self.assertTrue(issubclass(C, (A,)))

    def test_registration_edge_cases(self):


        class A(metaclass=abc.ABCMeta):
            pass
        A.register(A)


        class A1(A):
            pass
        self.assertRaises(RuntimeError, A1.register, A)


        class B(object):
            pass
        A1.register(B)
        A1.register(B)


        class C(A):
            pass
        A.register(C)
        self.assertRaises(RuntimeError, C.register, A)
        C.register(B)

    def test_register_non_class(self):


        class A(metaclass=abc.ABCMeta):
            pass
        self.assertRaisesRegex(TypeError, 'Can only register classes', A.
            register, 4)

    def test_registration_transitiveness(self):


        class A(metaclass=abc.ABCMeta):
            pass
        self.assertTrue(issubclass(A, A))
        self.assertTrue(issubclass(A, (A,)))


        class B(metaclass=abc.ABCMeta):
            pass
        self.assertFalse(issubclass(A, B))
        self.assertFalse(issubclass(A, (B,)))
        self.assertFalse(issubclass(B, A))
        self.assertFalse(issubclass(B, (A,)))


        class C(metaclass=abc.ABCMeta):
            pass
        A.register(B)


        class B1(B):
            pass
        self.assertTrue(issubclass(B1, A))
        self.assertTrue(issubclass(B1, (A,)))


        class C1(C):
            pass
        B1.register(C1)
        self.assertFalse(issubclass(C, B))
        self.assertFalse(issubclass(C, (B,)))
        self.assertFalse(issubclass(C, B1))
        self.assertFalse(issubclass(C, (B1,)))
        self.assertTrue(issubclass(C1, A))
        self.assertTrue(issubclass(C1, (A,)))
        self.assertTrue(issubclass(C1, B))
        self.assertTrue(issubclass(C1, (B,)))
        self.assertTrue(issubclass(C1, B1))
        self.assertTrue(issubclass(C1, (B1,)))
        C1.register(int)


        class MyInt(int):
            pass
        self.assertTrue(issubclass(MyInt, A))
        self.assertTrue(issubclass(MyInt, (A,)))
        self.assertIsInstance(42, A)
        self.assertIsInstance(42, (A,))

    def test_all_new_methods_are_called(self):


        class A(metaclass=abc.ABCMeta):
            pass


        class B(object):
            counter = 0

            def __new__(cls):
                B.counter += 1
                return super().__new__(cls)


        class C(A, B):
            pass
        self.assertEqual(B.counter, 0)
        C()
        self.assertEqual(B.counter, 1)


class TestABCWithInitSubclass(unittest.TestCase):

    def test_works_with_init_subclass(self):
        saved_kwargs = {}


        class ReceivesClassKwargs:

            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__()
                saved_kwargs.update(kwargs)


        class Receiver(ReceivesClassKwargs, abc.ABC, x=(1), y=(2), z=(3)):
            pass
        self.assertEqual(saved_kwargs, dict(x=1, y=2, z=3))


if __name__ == '__main__':
    unittest.main()
