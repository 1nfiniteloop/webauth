from application.messaging import (
    Observable,
    Observer,
    Message
)


class ObservableTopic(Observable):

    def __init__(self):
        self._observers = []

    def subscribe(self, observer: Observer):
        self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> bool:
        if observer in self._observers:
            self._observers.remove(observer)
            unsubscribed = True
        else:
            unsubscribed = False
        return unsubscribed

    def is_subscribed(self, observer: Observer) -> bool:
        return observer in self._observers

    @property
    def subscribers(self) -> list:
        return self._observers

    def notify(self, msg: Message):
        for observer in self._observers:
            observer.notify(msg)

