from threading import Event

_active_generations = {}


def create_generation(generation_id: str):
    event = Event()
    _active_generations[generation_id] = event
    return event


def cancel_generation(generation_id: str):
    if generation_id in _active_generations:
        _active_generations[generation_id].set()


def is_cancelled(generation_id: str):
    event = _active_generations.get(generation_id)

    if event:
        return event.is_set()

    return False


def cleanup_generation(generation_id: str):
    _active_generations.pop(generation_id, None)