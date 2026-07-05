from typing import Dict, Any, Optional
from backend.tools.search import load_dataset

def get_entity_details(entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves full details of a specific entity by its ID from the JSON dataset.
    Returns None if the entity is not found.
    """
    try:
        entities = load_dataset(entity_type)
    except ValueError:
        return None
        
    for entity in entities:
        if str(entity.get("id")).strip().upper() == str(entity_id).strip().upper():
            return entity
            
    return None
