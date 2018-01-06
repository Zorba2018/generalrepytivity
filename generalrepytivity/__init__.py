# -*- coding: utf-8 -*-

"""Top-level package for General Repytivity."""

__author__ = """Miguel Gonzalez Duque"""
__email__ = 'miguelgondu@gmail.com'
__version__ = '0.1.0'


import sympy
import itertools

def get_all_multiindices(p, n):
    '''
    This function returns a list of all the tuples of the form (a_1, ..., a_p)
    with a_i between 1 and n-1. These tuples serve as multiindices for tensors.

    To-Do: I could just return the itertools.product iterable object, no?
    '''
    return list(itertools.product(range(n), repeat=p))

def is_multiindex(multiindex, n, c_dimension):
    '''
    This function determines if a tuple is a multiindex or not
    according to these rules:
    1. () is a multiindex of length 0 (i.e. if the covariant or contravariant dimension
    is 0, the empty tuple is the only 0-multiindex)
    2. The length of a multiindex must be equal to the c_dimension
    3. Each value in the multiindex varies between 0 and n-1.
    '''
    if isinstance(multiindex, tuple):
        if len(multiindex) != c_dimension:
            return False
        for value in multiindex:
            if isinstance(value, int) or isinstance(value, float):
                if value < 0 or value >= n:
                    return False
            else:
                return False
        return True
    else:
        return False

def _get_matrix_of_basis_change(basis1, basis2, _dict, jacobian=True):
    '''
    This is an internal function. It is used in the change_basis method
    for tensor objects. It computes the matrix that represents the
    identity function from (V, basis1) to (V, basis2). It does so
    using derivatives.

    For example, for the variables

    basis1 = [e0, e1, e2, e3]
    basis2 = [f0, f1, f2, f3]
    _dict = {
        e0: f0 + f1,
        e1: f1,
        e2: f1 + f3,
        e3: f2
    }

    the resulting matrix would be
    [[1, 1, 0, 0],
     [0, 1, 0, 0],
     [0, 1, 0, 1],
     [0, 0, 1, 0]]

    if the jacobian keyword is set to True, and its transpose if
    it is false.
    '''

    dim = len(basis1)
    L = sympy.zeros(dim)
    for i in range(dim):
        for j in range(dim):
            if jacobian == True:
                L[i, j] = _dict[basis1[i]].diff(basis2[j])
            if jacobian == False:
                L[i,j] = _dict[basis1[j]].diff(basis2[i])
    if L.det() == 0:
        raise ValueError('The transformation is not invertible.')
    return L

def _is_valid_key(key, dim, ct_dim, c_dim):
    '''
    This is an internal function, it checks whether a given key (i.e. a pair
    of multiindices) is a valid key for certain dimension dim, contravariant dimension
    ct_dim and covariant dimension c_dim. It does so using the is_multiindex function.
    '''
    if len(key) != 2:
        return False
    a, b = key
    if not is_multiindex(a, dim, ct_dim):
        return False
    if not is_multiindex(b, dim, c_dim):
        return False

    return True

def _dict_completer_for_tensor(_dict, _type, dim):
    '''
    This function checks that the _dict is in proper form and completes in certain cases.
    Those cases are:
        - If one of the dimensions is 0, it is allowed to put only one multiindex instead
          of a pair.
        - if one of the dimensions is 1, it is allowd to put an integer instead of a
          1-multiindex.
    '''
    ct_dim = _type[0]
    c_dim = _type[1]

    new_dict = {}

    if _dict == {}:
        new_dict = {
            (tuple(0 for i in range(ct_dim)), tuple(0 for i in range(c_dim))): 0
        }
        return new_dict

    if ct_dim > 0 and c_dim == 0:
        for key in _dict:
            if _is_valid_key(key, dim, ct_dim, c_dim):
                new_dict[key] = _dict[key]
            elif ct_dim == 1 and isinstance(key, int):
                new_dict[((key, ), ())] = _dict[key]
            elif is_multiindex(key, dim, ct_dim):
                new_dict[(key, ())] = _dict[key]
            else:
                raise ValueError('Can\'t extend the key {} because it isn\'t a {}-multiindex'.format(
                    key, ct_dim))
        return new_dict

    if ct_dim == 0 and c_dim > 0:
        for key in _dict:
            if _is_valid_key(key, dim, ct_dim, c_dim):
                new_dict[key] = _dict[key]
            elif c_dim == 1 and isinstance(key, int):
                new_dict[(), (key, )] = _dict[key]
            elif is_multiindex(key, dim, c_dim):
                new_dict[((), key)] = _dict[key]
            else:
                raise ValueError('Can\'t extend the key {} because it isn\'t a {}-multiindex'.format(
                    key, c_dim))
        return new_dict

    if ct_dim == 1 and c_dim > 0:
        for key in _dict:
            if _is_valid_key(key, dim, ct_dim, c_dim):
                new_dict[key] = _dict[key]
            elif len(key) == 2:
                i, b = key
                if isinstance(i, int) and isinstance(b, int):
                    new_dict[((i, ), (b, ))] = _dict[key]
                elif isinstance(i, int) and is_multiindex(b, dim, c_dim):
                    new_dict[(i, ), b] = _dict[key]
                else:
                    raise ValueError('{} should be an integer and {} should be a {}-multiindex (or int in case 1).'.format(
                                                                            i, b, c_dim))
            else:
                raise ValueError('There should only be two things in {}'.format(key))
        return new_dict

    if ct_dim > 0 and c_dim == 1:
        for key in _dict:
            if _is_valid_key(key, dim, ct_dim, c_dim):
                new_dict[key] = _dict[key]
            elif len(key) == 2:
                a, j = key
                if isinstance(a, int) and isisntance(j, int):
                    new_dict[(a, ), (j, )] = _dict[key]
                elif is_multiindex(a, dim, ct_dim) and isinstance(j, int):
                    new_dict[a, (j, )] = _dict[key]
                else:
                    raise ValueError('{} should be an integer and {} should be a {}-multiindex (or int in case 1).'.format(
                                                                                                j, a, ct_dim))
        return new_dict

    for key in _dict:
        if not _is_valid_key(key, dim, ct_dim, c_dim):
            raise ValueError('Key {} is not compatible with the dimensions')

    return _dict

class Tensor:
    '''
    This class represents a tensor object in a given basis.

    To construct a (p,q)-Tensor, one must pass three arguments:
    1. basis: a list of sympy symbols which represent the coordinates (or
       basis of tangent space).
    1. _type: a pair of values p (the contravariant dimension) and q (the
      covariant dimension).
    2. the non-zero values, which is a dict whose keys are pairs of the
    form (a, b) where a and b are multi-indices such that $\Gamma^a_b = value$,
    the values that don't appear in this dict are assumed to be 0.
    '''
    def __init__(self, basis, _type, values):
        self.basis = basis
        self.ct_dim = _type[0]
        self.c_dim = _type[1]
        self.type = _type
        self.dim = len(self.basis)
        if values == 'zero':
            self.values = {
                (tuple(0 for i in range(self.ct_dim)), tuple(0 for i in range(self.c_dim))): 0
            }
        else:
            self.values = _dict_completer_for_tensor(values, self.type, self.dim)

    def __eq__(self, other):
        if other == 0:
            if set(self.values.values()) == set([0]):
                return True
            else:
                return False
        if not isinstance(other, Tensor):
            return False
        if self.basis == other.basis:
            if self.type == other.type:
                if self.get_all_values() == other.get_all_values():
                    return True
        return False

    def __getitem__(self, pair):
        if self.ct_dim == 0 and self.c_dim > 0:
            if is_multiindex(pair, self.dim, self.c_dim):
                if ((), pair) in self.values:
                    return sympy.simplify(self.values[((), pair)])
                else:
                    return sympy.simplify(0)

        if self.c_dim == 0 and self.ct_dim > 0:
            if is_multiindex(pair, self.dim, self.ct_dim):
                if (pair, ()) in self.values:
                    return sympy.simplify(self.values[(pair, ())])
                else:
                    return sympy.simplify(0)

        if self.c_dim == 1 and self.ct_dim == 1:
            if len(pair) == 2:
                i, j = pair
                if isinstance(i, int) and isinstance(j, int):
                    if ((i, ), (j, )) in self.values:
                        return sympy.simplify(self.values[(i, ), (j, )])
                    else:
                        return sympy.simplify(0)
            else:
                raise KeyError('There should be two things in {}, but there are {}'.format(pair, len(pair)))

        a, b = pair
        if isinstance(a, int):
            if isinstance(b, int):
                if (is_multiindex((a, ), self.dim, self.ct_dim) and
                    is_multiindex((b, ), self.dim, self.c_dim)):
                    if ((a, ), (b, )) in self.values:
                        return sympy.simplify(self.values[((a, ), (b, ))])
                    else:
                        return sympy.simplify(0)
                else:
                    raise KeyError('There\'s a problem with the multiindices ({}, ) and ({}, )'.format(a, b))
            if is_multiindex(b, self.dim, self.c_dim):
                if ((a, ), b) in self.values:
                    return sympy.simplify(self.values[((a, ), b)])
                else:
                    return sympy.simplify(0)
            else:
                raise KeyError('There\'s a problem with multiindex {}'.format(b))
        if is_multiindex(a, self.dim, self.ct_dim):
            if isinstance(b, int):
                if (a, (b, )) in self.values:
                    return sympy.simplify(self.values[(a, (b, ))])
                else:
                    return sympy.simplify(0)
            if is_multiindex(b, self.dim, self.c_dim):
                if (a, b) in self.values:
                    return sympy.simplify(self.values[(a, b)])
                else:
                    return sympy.simplify(0)
        raise KeyError('There\'s something wrong with the pair of multiindices {} and {}'.format(a, b))

    def __repr__(self):
        if set(self.values.values()) == set([0]):
            return '0'
        string = ''
        for key in self.values:
            string += '({})'.format(self.values[key])
            a, b = key
            if a != ():
                substring_of_a = ''
                for ind in a:
                    substring_of_a += '{} \\otimes '.format(self.basis[ind])
                substring_of_a = substring_of_a[:-len(' \\otimes ')]
                string += substring_of_a
            if b != ():
                if a != ():
                    string += ' \\otimes '
                for ind in b:
                    string += '{}* \\otimes '.format(self.basis[ind])
                string = string[:-len(' \\otimes ')]
            string += ' + '
        string = string[:-3]
        return string

    def _repr_latex_(self):
        if set(self.values.values()) == set([0]):
            return '$0$'
        string = '$'
        for key in self.values:
            string += '({})'.format(sympy.latex(self.values[key]))
            a, b = key
            if a != ():
                substring_of_a = ''
                for ind in a:
                    substring_of_a += '\\partial/\\partial {} \\otimes '.format(sympy.latex(self.basis[ind]))
                substring_of_a = substring_of_a[:-len(' \\otimes ')]
                string += substring_of_a
            if b != ():
                if a != ():
                    string += ' \\otimes '
                for ind in b:
                    string += 'd{} \\otimes '.format(self.basis[ind])
                string = string[:-len(' \\otimes ')]
            string += ' + '
        string = string[:-3]
        return (string + '$').replace('**', '^')

    def __add__(self, other):
        if other == 0:
            return Tensor(self.basis, self.type, self.values)
        if not isinstance(other, Tensor):
            raise ValueError('Cannot add a tensor with a {}'.format(type(other)))

        if other.basis != self.basis or other.type != self.type:
            raise ValueError('Tensors should be of the same type and have the same basis.')

        result_dict = self.values.copy()
        for key in other.values:
            if key in result_dict:
                result_dict[key] = result_dict[key] + other.values[key]
            if key not in result_dict:
                result_dict[key] = other.values[key]

        for key in result_dict.copy():
            if result_dict[key] == 0:
                empty = result_dict.pop(key)

        result_basis = self.basis
        result_type = self.type
        return Tensor(result_basis, result_type, result_dict).simplify()

    def __mul__(self, other):
        if self.type == (0,0):
            if isinstance(other, Tensor):
                if other.basis != self.basis:
                    raise ValueError('The basis of {} should be the same as the other tensor'.format(other))
                new_dict = other.values.copy()
                for key in other.values:
                    new_dict[key] = new_dict[key] * self.values[((), ())]
                return Tensor(self.basis, other.type, new_dict).simplify()
        if (isinstance(other, int) or isinstance(other, float)):
            new_dict = self.values.copy()
            for key in self.values:
                new_dict[key] = self.values[key] * other
            return Tensor(self.basis, self.type, new_dict).simplify()

        if isinstance(other, Tensor):
            if other.type != (0,0):
                raise ValueError('Can\'t multiply a tensor with a tensor that isn\'t (0,0)')
            if other.basis != self.basis:
                raise ValueError('The basis of {} should be the same as the other tensor'.format(other))

            other_value = other[(), ()]
            new_dict = self.values.copy()
            for key in self.values:
                new_dict[key] = self.values[key] * other_value
            return Tensor(self.basis, self.type, new_dict).simplify()

        try:
            new_dict = self.values.copy()
            for key in self.values:
                new_dict[key] = self.values[key] * other
            return Tensor(self.basis, self.type, new_dict).simplify()
        except:
            raise ValueError('Can\'t multiply a tensor with {}'.format(other))

    __rmul__ = __mul__

    def subs(self, list_of_substitutions):
        new_dict = {}
        for key, value in self.values.items():
            new_dict[key] = sympy.simplify(value).subs(list_of_substitutions)
        return Tensor(self.basis, self.type, new_dict).simplify()

    def simplify(self):
        '''
        This function simplifies (using sympy.simplify) every value in
        the tensors dict.

        For example:
        '''
        new_dict = {}
        for key, value in self.values.items():
            new_dict[key] = sympy.simplify(value)
        if Tensor == 0:
            return Tensor(self.basis, self.type, 'zero')
        return Tensor(self.basis, self.type, new_dict)

    def evalf(self):
        '''
        This function evaluates to floats every value in the tensors dict.
        '''
        new_dict = {}
        for key, value in self.values.items():
            new_dict[key] = sympy.simplify(self.values[key]).evalf()
        return Tensor(self.basis, self.type, new_dict)

    def get_all_values(self):
        '''
        This function returns a non-sparse values dict of the tensor (i.e.
        it fills all the missing zero values).
        '''
        new_dict = {}
        dim = self.dim
        contravariant_multiindices = get_all_multiindices(self.ct_dim, dim)
        covariant_multiindices = get_all_multiindices(self.c_dim, dim)
        for a in contravariant_multiindices:
            for b in covariant_multiindices:
                if (a,b) in self.values:
                    new_dict[a, b] = self.values[a, b]
                else:
                    new_dict[a, b] = 0
        return new_dict

    def change_basis(self, new_basis, basis_change):
        '''
        This function returns a new tensor object in the new basis according
        to the transormations stored in the dict basis_change.
        '''
        L = _get_matrix_of_basis_change(self.basis, new_basis, basis_change, False)
        contravariant_indices = get_all_multiindices(self.ct_dim, self.dim)
        covariant_indices = get_all_multiindices(self.c_dim, self.dim)
        new_tensor = Tensor(new_basis, self.type, 'zero')
        for key in self.values:
            c, d = key
            for a in contravariant_indices:
                for b in covariant_indices:
                    m = self.values[key]
                    for i in range(self.ct_dim):
                        m *= L[a[i], c[i]]
                    for j in range(self.c_dim):
                        m *= (L.T)[b[j], d[j]]
                    temp_tensor_values = {
                        (a, b): m
                    }
                    temp_tensor = Tensor(new_basis, self.type, temp_tensor_values)
                    new_tensor += temp_tensor
        return new_tensor

    def change_coordinates(self, new_coordinates, coord_change):
        '''
        This function returns a new tensor object in the new basis according
        to the transormations stored in the dict coord_change.
        '''
        L = _get_matrix_of_basis_change(self.basis, new_coordinates, coord_change, True)
        contravariant_indices = get_all_multiindices(self.ct_dim, self.dim)
        covariant_indices = get_all_multiindices(self.c_dim, self.dim)
        new_tensor = Tensor(new_coordinates, self.type, 'zero')
        for key in self.values:
            c, d = key
            for a in contravariant_indices:
                for b in covariant_indices:
                    m = self.values[key]
                    for i in range(self.ct_dim):
                        m *= L[a[i], c[i]]
                    for j in range(self.c_dim):
                        m *= (L.T)[b[j], d[j]]
                    temp_tensor_values = {
                        (a, b): m
                    }
                    temp_tensor = Tensor(new_coordinates, self.type, temp_tensor_values)
                    new_tensor += temp_tensor
        return new_tensor

    @classmethod
    def from_function(cls, basis, _type, func):
        '''
        This method allows you to create a tensor from a function. The function func must
        take 2 multiindices and turn them into a value.

        For example:
        def func(a, b):
            return 2**a[0] * 3**b[0] * 5**b[1]
        is a valid function for a (1,2)-Tensor.
        '''
        ct_dim, c_dim = _type
        dim = len(basis)
        ct_indices = get_all_multiindices(ct_dim, dim)
        c_indices = get_all_multiindices(c_dim, dim)
        values = {
            (a,b): func(a,b) for a in ct_indices for b in c_indices if func(a,b) != 0
        }
        return cls(basis, _type, values)

def get_tensor_from_matrix(matrix, basis):
    '''
    This function takes a square matrix and a basis and retruns a (0,2)-tensor in that basis.
    '''
    values = {}
    for i in range(len(matrix.tolist())):
        for j in range(len(matrix.tolist())):
            if matrix[i, j] != 0:
                values[(), (i,j)] = matrix[i, j]
    return Tensor(basis, (0, 2), values).simplify()

def get_matrix_from_tensor(tensor):
    '''
    This function takes an (0,2)-tensor and returns it matrix representation.
    '''
    matrix = sympy.zeros(len(tensor.basis))
    for i in range(len(tensor.basis)):
        for j in range(len(tensor.basis)):
            matrix[i, j] = tensor[(), (i,j)]

    return matrix

def contract_indices(tensor, i, j):
    '''
    Returns the resulting tensor of formally contracting the indices i and j
    of the given tensor.
    '''
    dim = len(tensor.basis)
    c_dim = tensor.c_dim
    ct_dim = tensor.ct_dim
    if c_dim < 1 or ct_dim < 1:
        raise ValueError('One of the dimensions in the type {} is less than one.'.format(tensor.type))
    if i < 0 or i >= ct_dim:
        raise ValueError('{} is either negative or bigger than the contravariant dimension minus one {}'.format(i,
                                                                                    ct_dim-1))
    if j < 0 or j >= c_dim:
        raise ValueError('{} is either negative or bigger than the covariant dimension minus one {}'.format(j,
                                                                                    c_dim-1))

    contravariant_indices = get_all_multiindices(ct_dim-1, dim)
    covariant_indices = get_all_multiindices(c_dim-1, dim)
    new_tensor_dict = {}
    for a in contravariant_indices:
        for b in covariant_indices:
            sumand = 0
            for r in range(dim):
                if a != ():
                    a_extended = a[:i] + (r, ) + a[i:]
                if a == ():
                    a_extended = (r, )
                if b != ():
                    b_extended = b[:j] + (r, ) + b[j:]
                if b == ():
                    b_extended = (r, )
                sumand += tensor[a_extended, b_extended]
            if sumand != 0:
                new_tensor_dict[a, b] = sumand

    return Tensor(tensor.basis, (ct_dim - 1, c_dim - 1), new_tensor_dict).simplify()

def lower_index(tensor, metric, i):
    if isinstance(metric, Tensor):
        if metric.basis != tensor.basis:
            raise ValueError('Tensor and Metric should be on the same basis.')
        if metric.type != (0,2):
            raise ValueError('metric should be a (0,2)-tensor')
    else:
        raise ValueError('metric should be a (0,2)-tensor')

    if tensor.ct_dim == 0:
        raise ValueError('There\'s no index to be lowered.')

    if i < 0 or i >= tensor.ct_dim:
        raise ValueError('The index to be lowered ({}) must be between 0 and {}'.format(i,
                                                                        tensor.ct_dim))

    basis = tensor.basis
    dim = tensor.dim
    new_ct_dim = tensor.ct_dim - 1
    new_c_dim = tensor.c_dim + 1
    new_type = (new_ct_dim, new_c_dim)
    contravariant_indices = get_all_multiindices(new_ct_dim, dim)
    covariant_indices = get_all_multiindices(new_c_dim, dim)

    new_tensor_dict = {}
    for a in contravariant_indices:
        for b in covariant_indices:
            value = 0
            for r in range(dim):
                if a == ():
                    a_extended = (r, )
                if a != ():
                    a_extended = a[:i] + (r, ) + a[i:]
                b_reduced = b[1:]
                value += metric[(), (b[0], r)]*tensor[a_extended, b_reduced]
            if value != 0:
                new_tensor_dict[a, b] = value

    return Tensor(basis, new_type, new_tensor_dict).simplify()

def raise_index(tensor, metric, j):
    '''

    '''
    if isinstance(metric, Tensor):
        if metric.basis != tensor.basis:
            raise ValueError('Tensor and Metric should be on the same basis.')
        if metric.type != (0,2):
            raise ValueError('metric should be an (0,2)-tensor.')
    else:
        raise ValueError('metric should be an (0,2)-tensor.')

    if tensor.c_dim == 0:
        raise ValueError('There\'s no index to be lowered.')

    if j < 0 or j >= tensor.c_dim:
        raise ValueError('The index to be raised ({}) must be between 0 and {}'.format(j,
                                                                        tensor.c_dim))

    basis = tensor.basis
    dim = len(basis)
    new_ct_dim = tensor.ct_dim + 1
    new_c_dim = tensor.c_dim - 1
    new_type = (new_ct_dim, new_c_dim)
    contravariant_indices = get_all_multiindices(new_ct_dim, dim)
    covariant_indices = get_all_multiindices(new_c_dim, dim)
    inverse_metric_matrix = get_matrix_from_tensor(metric).inv()

    new_tensor_dict = {}
    for a in contravariant_indices:
        for b in covariant_indices:
            value = 0
            for r in range(dim):
                # Here, a[-1] is b_j.
                a_reduced = a[:-1]
                if b == ():
                    b_expanded = (r, )
                if b != ():
                    b_expanded = b[:j] + (r, ) + b[j:]
                value += inverse_metric_matrix[a[-1], r]*tensor[a_reduced, b_expanded]
            if value != 0:
                new_tensor_dict[a, b] = value

    # if new_tensor_dict == {}:
    #     new_tensor_dict = {(a, b): 0 for a in contravariant_indices for b in covariant_indices}

    return Tensor(basis, new_type, new_tensor_dict).simplify()

def _symmetry_completer(_dict):
    new_dict = _dict.copy()
    for a, b in _dict.keys():
        inverted_b = (b[1], b[0])
        if (a, inverted_b) in new_dict:
            if new_dict[a, b] != new_dict[a, inverted_b]:
                raise ValueError('Inconsistent values for pairs {} and {} of subindices'.format(b, inverted_b))
        if (a, inverted_b) not in new_dict:
            new_dict[a, inverted_b] = new_dict[a, b]
    return new_dict

def _dict_completer(_dict, c_dimension, ct_dimension, dim):
    c_indices = get_all_multiindices(c_dimension, dim)
    ct_indices = get_all_multiindices(ct_dimension, dim)
    new_dict = _symmetry_completer(_dict)
    for a in c_indices:
        for b in ct_indices:
            if (a,b) in new_dict:
                pass
            if (a,b) not in new_dict:
                new_dict[a,b] = 0
    return new_dict

def get_chrisoffel_symbols_from_metric(metric):
    basis = metric.basis
    dim = len(basis)
    metric_matrix = get_matrix_from_tensor(metric)
    inverse_metric_matrix = metric_matrix.inv()
    contravariant_indices = get_all_multiindices(1, dim)
    covariant_indices = get_all_multiindices(2, dim)
    values = {}
    for a in contravariant_indices:
        for b in covariant_indices:
            i, j = b
            c = a[0]
            sumand = 0
            for r in range(dim):
                L = (metric_matrix[j, r].diff(basis[i])
                     + metric_matrix[i, r].diff(basis[j])
                     - metric_matrix[i, j].diff(basis[r]))
                sumand += inverse_metric_matrix[r, c] * L
            if sumand != 0:
                values[a, b] = (1/2) * sumand
    return Tensor(basis, (1,2), values).simplify()

def get_Riemann_tensor(christoffel_symbols):
    cs = christoffel_symbols
    basis = christoffel_symbols.basis
    dim = len(christoffel_symbols.basis)
    contravariant_indices = get_all_multiindices(1, dim)
    covariant_indices = get_all_multiindices(3, dim)
    values = {}
    for x in contravariant_indices:
        for y in covariant_indices:
            d = x[0]
            c, a, b = y
            sumand = cs[d, (b,c)].diff(basis[a]) - cs[d, (a,c)].diff(basis[b])
            for u in range(dim):
                sumand += cs[d, (a, u)]*cs[u, (c,b)] - cs[d, (b, u)]*cs[u, (c, a)]
            if sumand != 0:
                values[x, y] = sumand
    return Tensor(cs.basis, (1, 3), values).simplify()

def get_Ricci_tensor(christoffel_symbols, Riem=None):
    if Riem == None:
        Riem = get_Riemann_tensor(christoffel_symbols)
    return contract_indices(Riem, 0, 1)

def get_scalar_curvature(christoffel_symbols, metric, Ric=None):
    if Ric == None:
        Ric = get_Ricci_tensor(christoffel_symbols)
    Temp = raise_index(Ric, metric, 0)
    return contract_indices(Temp, 0, 0)

def get_Einstein_tensor(christoffel_symbols, metric, Ric=None, R=None):
    if Ric == None:
        Ric = get_Ricci_tensor(christoffel_symbols)
    if R == None:
        R = get_scalar_curvature(christoffel_symbols, metric)
    g = metric
    return Ric + (-1/2)*R*g

def _get_preimage(_dict, value):
    list_of_preimages = [key for (key, _value) in _dict.items() if _value == value]
    return list_of_preimages

def _get_list_of_lines(tensor, symbol):
    list_of_lines = []
    if isinstance(tensor, Tensor):
        for value in set(tensor.values.values()):
            if value != 0:
                list_of_preimages = _get_preimage(tensor.values, value)
                line = '$$'
                for preimage in list_of_preimages:
                    a, b = preimage
                    line += symbol + '^{'
                    for i in a:
                        line += str(i)
                    line += '}_{'
                    for j in b:
                        line += str(j)
                    line += '} = '
                line += sympy.latex(value)
                line += '$$\n'
                list_of_lines.append(line)

        # Last line, the one about the zeros
        if list_of_lines != []:
            line = '$$' + symbol + '^{'
            for k in range(tensor.ct_dim):
                line += 'a_{' + str(k) + '}'
            line += '}_{'
            for k in range(tensor.c_dim):
                line += 'b_{' + str(k) + '}'
            line += '} = 0 \mbox{ in any other case' + '}$$\n'
            list_of_lines.append(line)
        if list_of_lines == []:
            line = '$$' + symbol + '^{'
            for k in range(tensor.ct_dim):
                line += 'a_{' + str(k) + '}'
            line += '}_{'
            for k in range(tensor.c_dim):
                line += 'b_{' + str(k) + '}'
            line += '} = 0 \mbox{ in every case' + '}$$\n'
            list_of_lines.append(line)
    else:
        list_of_lines.append('$$' + symbol + ' = ' + str(tensor) + '$$')
    return list_of_lines

def print_in_file(file_name, tensor, symbol, append_flag=False, _format='txt'):
    if not append_flag:
        try:
            _file = open(file_name, 'x')
        except:
            _file = open(file_name, 'w')
    if append_flag:
        _file = open(file_name, 'a')

    list_of_lines = _get_list_of_lines(tensor, symbol)

    if _format == 'txt':
        _file.writelines(list_of_lines)
        _file.close()
    elif _format == 'tex':
        complete_list_of_lines = []
        complete_list_of_lines.append('\\documentclass{article' + '}\n')
        complete_list_of_lines.append('\\usepackage[utf8]{inputenc' + '}\n')
        complete_list_of_lines.append('\\usepackage[T1]{fontenc' + '}\n')
        complete_list_of_lines.append('\\usepackage[english]{babel' + '}\n')
        complete_list_of_lines.append('\\usepackage{amsmath' + '}\n')
        complete_list_of_lines.append('\\usepackage{amssymb' + '}\n')
        complete_list_of_lines.append('\n')
        complete_list_of_lines.append('\\begin{document' + '}\n')
        complete_list_of_lines.append('\n')
        complete_list_of_lines += list_of_lines
        complete_list_of_lines.append('\n')
        complete_list_of_lines.append('\\end{document' + '}\n')
        _file.writelines(complete_list_of_lines)
        _file.close()
    else:
        raise ValueError('Expected txt or tex for format, but got {}'.format(_format))

class Spacetime:
    def __init__(self, _metric, printing_flag=False):
        s, t, x, y, z = sympy.symbols('s t x y z')
        self.metric = _metric
        self.basis = _metric.basis
        if printing_flag:
            print('Computing Christoffel Symbols')
        self.christoffel_symbols = get_chrisoffel_symbols_from_metric(_metric)
        if printing_flag:
            print('Computing Riemann tensor')
        self.Riem = get_Riemann_tensor(self.christoffel_symbols)
        if printing_flag:
            print('Computing Ricci tensor')
        self.Ric = get_Ricci_tensor(self.christoffel_symbols, self.Riem)
        if printing_flag:
            print('Computing Scalar Curvature')
        self.R = get_scalar_curvature(self.christoffel_symbols, self.metric, self.Ric)[(), ()]
        if printing_flag:
            print('Computing Einstein\'s tensor')
        self.G = get_Einstein_tensor(self.christoffel_symbols, self.metric, self.Ric, self.R)

    def print_summary(self, file_name='Spacetime.txt', _format='txt'):
        try:
            _file = open(file_name, 'x')
        except:
            _file = open(file_name, 'w')
        complete_list_of_lines = []

        #Metric
        complete_list_of_lines.append('Metric:\n')
        complete_list_of_lines += _get_list_of_lines(self.metric, 'g')
        complete_list_of_lines.append('\n')

        #Christoffel Symbols
        complete_list_of_lines.append('Christoffel Symbols:\n')
        complete_list_of_lines += _get_list_of_lines(self.christoffel_symbols, '\Gamma')
        complete_list_of_lines.append('\n')

        #Riemann Tensor
        complete_list_of_lines.append('Riemman tensor:\n')
        complete_list_of_lines += _get_list_of_lines(self.Riem, '\mbox{' + 'Riem' + '}')
        complete_list_of_lines.append('\n')

        #Ricci Tensor
        complete_list_of_lines.append('Ricci tensor:\n')
        complete_list_of_lines += _get_list_of_lines(self.Ric, '\mbox{' + 'Ric' + '}')
        complete_list_of_lines.append('\n')

        #Scalar curvature
        complete_list_of_lines.append('Scalar curvature:\n')
        complete_list_of_lines += _get_list_of_lines(self.R, '\mbox{' + 'R' + '}')
        complete_list_of_lines.append('\n')

        if _format == 'txt':
            _file.writelines(complete_list_of_lines)
            _file.close()
        elif _format == 'tex':
            final_list_of_lines = []
            final_list_of_lines.append('\\documentclass{article' + '}\n')
            final_list_of_lines.append('\\usepackage[utf8]{inputenc' + '}\n')
            final_list_of_lines.append('\\usepackage[T1]{fontenc' + '}\n')
            final_list_of_lines.append('\\usepackage[english]{babel' + '}\n')
            final_list_of_lines.append('\\usepackage{amsmath' + '}\n')
            final_list_of_lines.append('\\usepackage{amssymb' + '}\n')
            final_list_of_lines.append('\n')
            final_list_of_lines.append('\\begin{document' + '}\n')
            final_list_of_lines.append('\n')
            final_list_of_lines += complete_list_of_lines
            final_list_of_lines.append('\n')
            final_list_of_lines.append('\\end{document' + '}\n')
            _file.writelines(final_list_of_lines)
            _file.close()
        else:
            raise ValueError('Expected txt or tex for format, but got {}'.format(_format))