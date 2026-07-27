# app/exceptions/category_exceptions.py

from fastapi import HTTPException, status


class CategoryNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie introuvable",
        )


class CannotModifyDefaultCategoryException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de modifier ou supprimer une catégorie par défaut",
        )
        
class CategoryAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Une catégorie avec ce nom existe déjà",
        )