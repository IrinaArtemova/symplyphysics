from __future__ import annotations
from functools import partial
from typing import Callable, Sequence, TypeAlias
from sympy import Expr, sympify
from sympy.vector import Vector as SymVector

from .field_point import FieldPoint
from ..coordinate_systems.coordinate_systems import CoordinateSystem
from ..vectors.vectors import Vector
from ...core.dimensions import ScalarValue

FieldFunction: TypeAlias = Callable[[FieldPoint], Sequence[ScalarValue]] | Sequence[ScalarValue]


def _subs_with_point(expr: Sequence[ScalarValue], coordinate_system: CoordinateSystem,
    point_: FieldPoint) -> Sequence[Expr]:
    base_scalars = coordinate_system.coord_system.base_scalars()
    result: list[Expr] = []
    for e in expr:
        expression = sympify(e)
        for i, scalar in enumerate(base_scalars):
            expression = expression.subs(scalar, point_.coordinate(i))
        result.append(expression)
    return result


# Contains mapping of point to vector in _point_function, eg P(FieldPoint).
# Vector field is coordinate system dependent, because generally vectors are not coordinate
# system invariant.
class VectorField:
    # Can contain lambda or some value. If value is stored, it will be returned when field is applied.
    _point_function: FieldFunction
    #NOTE: 4 and higher dimensional fields are not supported cause of using CoordSys3D
    #      that allows rebasing vector field to different coordinate systems.
    _coordinate_system: CoordinateSystem

    def __init__(self,
        point_function: FieldFunction,
        coordinate_system: CoordinateSystem = CoordinateSystem(CoordinateSystem.System.CARTESIAN)):
        self._point_function = point_function
        self._coordinate_system = coordinate_system

    def __call__(self, point_: FieldPoint) -> Vector:
        result = self._point_function(point_) if callable(
            self._point_function) else self._point_function
        return Vector(result, self._coordinate_system)

    @property
    def basis(self) -> list[Expr]:
        return list(self._coordinate_system.coord_system.base_scalars())

    @property
    def coordinate_system(self) -> CoordinateSystem:
        return self._coordinate_system

    @property
    def field_function(self) -> FieldFunction:
        return self._point_function

    # Constructs new VectorField from Vector.
    @staticmethod
    def from_vector(vector_: Vector) -> VectorField:
        point_function = partial(_subs_with_point, vector_.components, vector_.coordinate_system)
        return VectorField(point_function, vector_.coordinate_system)

    # Constructs new VectorField from SymPy expression.
    # Can contain value instead of SymPy Vector, eg 0.5, but it should be sympified.
    @staticmethod
    def from_sympy_vector(sympy_vector_: SymVector,
        coordinate_system: CoordinateSystem) -> VectorField:
        field_vector = Vector.from_sympy_vector(sympy_vector_, coordinate_system)
        return VectorField.from_vector(field_vector)

    # Applies field to a trajectory / surface / volume - calls field functions with each element of the trajectory as parameter.
    # trajectory_ - list of expressions that correspond to a function in some space, eg [param, param] for a linear function y = x
    # return - vector parametrized by trajectory parameters.
    def apply(self, trajectory_: Sequence[Expr]) -> Vector:
        field_point = FieldPoint()
        for idx, element in enumerate(trajectory_):
            field_point.set_coordinate(idx, element)
        return self(field_point)

    # Convert coordinate system to space and apply field.
    # Applying field to entire space is necessary for SymPy field operators like Curl.
    # return - vector that depends on basis parameters.
    def apply_to_basis(self) -> Vector:
        return self.apply(self.basis)

    # Apply field to entire coordinate system and convert to SymPy vector
    def to_sympy_vector(self) -> SymVector:
        field_space = self.apply_to_basis()
        return field_space.to_sympy_vector()

    # rebase() for curvilinear coordinate systems is quite complex. Not implemented for the moment.
