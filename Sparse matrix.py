## Yeongjun "James" Park
## 22 March 2019

######################################
## Sparse matrix implementation 
######################################

import scipy

class MyCSR():
    def __init__(self, rows, cols, nnz=0, dtype=scipy.float64):
        self.shape = (rows, cols)
        self.dtype = dtype
        self.row_ptrs = scipy.zeros(rows+1, dtype=scipy.intp)
        self.col_indices = scipy.zeros(nnz, dtype=scipy.intp)
        self.data = scipy.zeros(nnz, dtype=dtype)
    
    def _build_row_ptrs(indices):
        self.row_ptrs[1:] = scipy.cumsum(scipy.bincount(indices, minlength=self.ncols))
    
    def _build_cols_data(element_generator):
        # element generator yields (row,col,data) for each nonzero element
        # this functions requires row_ptrs to be built in prior
        indices_used = scipy.zeros(self.ncols, dtype=scipy.intp)
        for row, col, data in element_generator:
            index = self.row_ptrs[row] + indices_used[row]
            indices_used[row] += 1
            
            self.col_indices[index] = col
            self.data[index] = data
    
    def _element_generator(self):
        for row in range(self.shape[0]):
            for index in range(*self.row_ptrs[row:row+2]):
                yield row, self.col_indices[index], self.data[index]
    
    def _row_element_generator(self, row):
        for index in range(*self.row_ptrs[row:row + 2]):
            col = self.col_indices[index]
            data = self.data[index]
            yield col, data

    def _right_mul_by_csr(self, other):
        l_nrows, l_ncols = self.shape
        r_nrows, r_ncols = other.shape
        prod_nrows = l_nrows
        prod_ncols = r_ncols
        
        if l_ncols != r_nrows:
            raise ValueError("Matrices being multiplied have incompatible sizes")
        
        ### First find the number of product nonzeros
        col_nonzero_found = scipy.zeros(r_ncols, dtype=scipy.bool_)
        total_nonzeros_found = 0
        for l_row in range(l_nrows):
            for l_col, l_data in self._row_element_generator(l_row):
                for r_col, r_data in other._row_element_generator(l_col):
                    if not col_nonzero_found[r_col]:
                        col_nonzero_found[r_col] = True
                        total_nonzeros_found += 1
            
            # Clear the flags in O(row nnzs) time
            for l_col, l_data in self._row_element_generator(l_row):
                for r_col, r_data in other._row_element_generator(l_col):
                    col_nonzero_found[r_col] = False
                    
        ### Allocate the new sparse matrix ###
        prod = MyCSR(prod_nrows, prod_ncols, nnz=total_nonzeros_found, dtype=self.dtype)
        
        ### Do the actual multiplication ###
        prod_row_data = scipy.zeros(prod_nrows, dtype=self.dtype)
        prod_index = 0
        for l_row in range(l_nrows):

            # Calculation Pass
            for l_col, l_data in self._row_element_generator(l_row):
                for r_col, r_data in other._row_element_generator(l_col):
                    prod_row_data[r_col] += r_data * l_data
                    
                    # Record column index, if this is a new nonzero product element
                    if not col_nonzero_found[r_col]:
                        prod.col_indices[prod_index] = r_col
                        
                        col_nonzero_found[r_col] = True
                        prod_index += 1
            
            # Finsh row_ptrs for this row (allow prod._row_element_generator to work, sort of)
            prod.row_ptrs[l_row + 1] = prod_index
            # Storage & Clearing Pass
            for other_prod_index in range(*prod.row_ptrs[l_row:l_row+2]):
                # Store data
                prod_col = prod.col_indices[other_prod_index]
                prod.data[other_prod_index] = prod_row_data[prod_col]
                # Clear row work arrays
                prod_row_data[prod_col] = 0
                col_nonzero_found[prod_col] = 0
        
        return prod
    
    def _right_mul_by_dense_matrix(self, other):
        assert(False)
    
    def _left_mul_by_dense_matrix(self, other):
        assert(False)
    
    def __matmul__(self, other):
        if isinstance(other, scipy.ndarray):
            if len(other.shape) == 1:
                if other.shape[0] == self.shape[1]:
                    result = scipy.zeros(self.shape[0])
                    for row, col, data in self._element_generator():
                        result[row] += data * other[col]
                else:
                    raise ValueError("multiplied matrix and vector have incompatible sizes")
            elif len(other.shape) == 2:
                if other.shape[0] == self.shape[1]:
                    result = _right_mul_by_dense(other)
                else:
                    raise ValueError("Matrices being multiplied have incompatible sizes")
        elif isinstance(other, MyCSR):
            result = self._right_mul_by_csr(other)
        else:
            TypeError("matrix multiplication not supported for this operand type")
        
        return result
    
    def __rmatmul__(self, other):
        if isinstance(other, scipy.ndarray):
            if len(other.shape) == 1:
                if other.shape[0] == self.shape[0]:
                    result = scipy.zeros(self.shape[1])
                    for row, col, data in self._element_generator():
                        result[col] += data * other[row]
                else:
                    raise ValueError("multiplied matrix and vector have incompatible sizes")
            elif len(other.shape) == 2:
                if other.shape[0] == self.shape[1]:
                    result = _left_mul_by_dense(other)
                else:
                    raise ValueError("Matrices being multiplied have incompatible sizes")
        elif isinstance(other, MyCSR):
            result = other._right_mul_by_csr(self)
        else:
            TypeError("matrix multiplication not supported for this operand type")
        
        return result