# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.event.eventmiddleware import EventMiddleware
from tuxemon.platform.events import PlayerInput


class DummyMiddleware(EventMiddleware):
    def preprocess(self, event: PlayerInput):
        return event

    def postprocess(self, processed_event: PlayerInput):
        return processed_event


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        EventMiddleware()


def test_subclass_must_implement_methods():
    mw = DummyMiddleware()
    event = PlayerInput(button="TEST", value=1, hold_time=0)
    assert mw.preprocess(event) is event
    assert mw.postprocess(event) is event


@pytest.mark.parametrize(
    "preprocess_return, postprocess_return, expected_pre, expected_post",
    [
        pytest.param(None, "event", None, "event", id="pre_none_post_event"),
        pytest.param("event", None, "event", None, id="pre_event_post_none"),
    ],
)
def test_consuming_middleware(
    preprocess_return, postprocess_return, expected_pre, expected_post
):
    class ConsumingMiddleware(EventMiddleware):
        def preprocess(self, event: PlayerInput):
            return preprocess_return if preprocess_return != "event" else event

        def postprocess(self, processed_event: PlayerInput):
            return (
                postprocess_return
                if postprocess_return != "event"
                else processed_event
            )

    mw = ConsumingMiddleware()
    event = PlayerInput(button="TEST", value=1, hold_time=0)

    pre = mw.preprocess(event)
    post = mw.postprocess(event)

    assert (pre is None) if expected_pre is None else (pre is event)
    assert (post is None) if expected_post is None else (post is event)
