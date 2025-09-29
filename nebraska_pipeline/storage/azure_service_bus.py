from azure.servicebus import (
    AutoLockRenewer,
    ServiceBusClient,
    ServiceBusReceivedMessage,
)

from nebraska_pipeline.utils.app_logs import log_handler


class AzureServiceBus:
    def __init__(self, service_bus_client: ServiceBusClient, queue_name: str):
        self.service_bus_client: ServiceBusClient = service_bus_client
        self.queue_name: str = queue_name

    def getMessageFromQueue(self) -> ServiceBusReceivedMessage | None:
        with (
            self.service_bus_client.get_queue_receiver(
                queue_name=self.queue_name,
            ) as client,
            AutoLockRenewer() as lock_renewer,
        ):
            messages = client.receive_messages(max_message_count=1, max_wait_time=5)
            if len(messages) == 0:
                return None
            msg = messages[0]
            lock_renewer.register(client, renewable=msg, max_lock_renewal_duration=300)
            log_handler.info(f"accuired lock look for : {msg.message_id}")
            return msg

    def acknowledgeMessage(self, msg: ServiceBusReceivedMessage) -> None:
        with self.service_bus_client.get_queue_receiver(
            queue_name=self.queue_name
        ) as client:
            client.complete_message(message=msg)
            log_handler.info(f"processing completed and deleted : {msg.message_id}")

    def addToDeadLetterQueue(
        self,
        msg: ServiceBusReceivedMessage,
    ) -> True:
        with self.service_bus_client.get_queue_receiver(
            queue_name=self.queue_name
        ) as client:
            client.dead_letter_message(message=msg)
            log_handler.info(f"processing completed and deleted : {msg.message_id}")
