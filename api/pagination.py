# api/pagination.py
from flask import request

def get_pagination_params(default_page=1, default_per_page=20, max_per_page=100):
    """
    Extract and validate pagination parameters from request args.
    
    Args:
        default_page (int): Default page number if not provided or invalid
        default_per_page (int): Default items per page if not provided or invalid
        max_per_page (int): Maximum allowed items per page
    
    Returns:
        tuple: (page, per_page) as integers
    """
    # Get page parameter
    try:
        page = int(request.args.get('page', default_page))
        if page < 1:
            page = default_page
    except (ValueError, TypeError):
        page = default_page
    
    # Get per_page parameter
    try:
        per_page = int(request.args.get('per_page', default_per_page))
        if per_page < 1:
            per_page = default_per_page
        # Enforce maximum limit
        if per_page > max_per_page:
            per_page = max_per_page
    except (ValueError, TypeError):
        per_page = default_per_page
    
    return page, per_page


def paginate_query(query, page, per_page):
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page (int): Page number (1-indexed)
        per_page (int): Items per page
    
    Returns:
        tuple: (paginated_query, total_items, total_pages)
    """
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division
    
    # Adjust page if it's out of bounds
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    offset = (page - 1) * per_page
    paginated_query = query.offset(offset).limit(per_page)
    
    return paginated_query, total_items, total_pages


# api/pagination.py - Update create_pagination_response function

def create_pagination_response(items, page, per_page, total_items, total_pages):
    """
    Create a standardized pagination response dictionary.
    
    Args:
        items: List of items for the current page
        page (int): Current page number
        per_page (int): Items per page
        total_items (int): Total number of items
        total_pages (int): Total number of pages
    
    Returns:
        dict: Pagination response
    """
    # Handle edge case where total_pages is 0 (no items)
    if total_pages == 0:
        has_next = False
        has_prev = False
    else:
        has_next = page < total_pages
        has_prev = page > 1
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev,
        'next_page': page + 1 if has_next else None,
        'prev_page': page - 1 if has_prev else None
    }
