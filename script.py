import json
import pika
from mongoengine import connect, Document, StringField, DateTimeField, ReferenceField, ListField

connect("Hw8", host="qw")

class Author(Document):
    fullname = StringField(required=True)
    born_date = DateTimeField()
    born_location = StringField()
    description = StringField()

class Quote(Document):
    tags = ListField(StringField())
    author = ReferenceField(Author)
    quote = StringField()

class Contact(Document):
    full_name = StringField(required=True)
    email = StringField(required=True)
    message_sent = StringField(default=False)

def load_data(file_name, model):
    with open(file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

    for item_data in data:
        item = model(**item_data)
        item.save()

load_data("authors.json", Author)
load_data("quotes.json", Quote)

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.queue_declare(queue="contacts_queue")
fake_contacts = [
    {"full_name": "John Doe", "email": "john@example.com"},
    {"full_name": "Jane Smith", "email": "jane@example.com"},
]

for contact_data in fake_contacts:
    contact = Contact(**contact_data)
    contact.save()

    channel.basic_publish(exchange="", routing_key="contacts_queue", body=str(contact.id))

connection.close()

def search_quotes(command):
    if command.startswith("name:"):
        author_name = command.split(":")[1].strip()
        author = Author.objects(fullname=author_name).first()
        if author:
            quotes = Quote.objects(author=author)
            return [quote.quote for quote in quotes]
        else:
            return ["Author not found."]
    elif command.startswith("tag:"):
        tag_name = command.split(":")[1].strip()
        quotes = Quote.objects(tags=tag_name)
        return [quote.quote for quote in quotes]
    elif command.startswith("tags:"):
        tag_names = command.split(":")[1].split(",")
        quotes = Quote.objects(tags__in=tag_names)
        return [quote.quote for quote in quotes]
    elif command == "exit":
        return ["Exiting the script."]
    else:
        return ["Invalid command."]

while True:
    user_command = input("Enter command (name: author_name, tag: tag_name, tags: tag1,tag2, exit): ")
    results = search_quotes(user_command)
    
    for result in results:
        print(result)
