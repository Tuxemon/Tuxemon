def entity_at_position(entity, event):
    """
    Only true if the entity is exactly in the center of the tile.
    Partially in/out the tile will be False.
    """
    return event.rect.topleft == entity.tile_pos
