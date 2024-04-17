from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
app = FastAPI()
from pydantic import BaseModel
import requests
import datetime

# models.Base.metadata.create_all(bind=engine)
# WhatsApp Business API configuration
API_URL = "https://graph.facebook.com/v15.0/your_phone_number_id/messages"
API_TOKEN = "445873704494591|_bYZae5i-7oI5DNc4rAWyLq1X40"

# Create a data model for incoming messages
class IncomingMessage(BaseModel):
    messaging_product: str
    contacts: list
    messages: list

# Create a data model for outgoing messages
class OutgoingMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str
    to: str
    type: str
    text: dict

# Customer data to simulate customer identification and data storage
customer_data = {}

# Pet, service, and slot data
pets = ["Dog", "Cat", "Bird"]
services = ["Basic Grooming", "Full Grooming"]
slots = ["10:00 AM", "2:00 PM", "4:00 PM"]
base_prices = {"Basic Grooming": 50, "Full Grooming": 100}
discount_day = "Saturday"
premium_day = "Monday"

# Function to send a message via the WhatsApp Business API
def send_message(outgoing_message: OutgoingMessage):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(API_URL, headers=headers, json=outgoing_message.dict())
    
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
    
    return response

# Function to process the incoming message
@app.post("/webhook")
async def webhook(request: Request):
    # Parse incoming request
    data = await request.json()
    print(data)
    incoming_message = IncomingMessage(**data)
    
    # Verify the incoming message is from WhatsApp
    if incoming_message.messaging_product != "whatsapp":
        raise HTTPException(status_code=400, detail="Invalid messaging product")
    
    # Process each incoming message
    for message in incoming_message.messages:
        contact_id = incoming_message.contacts[0]["wa_id"]
        message_body = message["text"]["body"]
        
        # Identify customer from the phone number (contact ID)
        if contact_id not in customer_data:
            customer_data[contact_id] = {
                "state": "start"
            }
        
        customer_state = customer_data[contact_id]["state"]
        
        # Handle the conversation based on the customer's current state
        if customer_state == "start":
            # Welcome the customer and ask for pet selection
            response_text = (
                "Welcome to our pet grooming service! Please select a pet:\n"
                "1. Dog\n"
                "2. Cat\n"
                "3. Bird\n"
                "Reply with the number of your choice."
            )
            customer_data[contact_id]["state"] = "select_pet"
        elif customer_state == "select_pet":
            # Handle pet selection
            if message_body == "1":
                customer_data[contact_id]["pet"] = "Dog"
            elif message_body == "2":
                customer_data[contact_id]["pet"] = "Cat"
            elif message_body == "3":
                customer_data[contact_id]["pet"] = "Bird"
            else:
                response_text = "Invalid choice. Please try again."
                send_message(OutgoingMessage(
                    recipient_type="individual",
                    to=contact_id,
                    type="text",
                    text={"body": response_text}
                ))
                continue
            
            # Ask for service selection
            response_text = (
                "Great! Please select a service:\n"
                "1. Basic Grooming\n"
                "2. Full Grooming\n"
                "Reply with the number of your choice."
            )
            customer_data[contact_id]["state"] = "select_service"
        elif customer_state == "select_service":
            # Handle service selection
            if message_body == "1":
                customer_data[contact_id]["service"] = "Basic Grooming"
            elif message_body == "2":
                customer_data[contact_id]["service"] = "Full Grooming"
            else:
                response_text = "Invalid choice. Please try again."
                send_message(OutgoingMessage(
                    recipient_type="individual",
                    to=contact_id,
                    type="text",
                    text={"body": response_text}
                ))
                continue
            
            # Ask for date selection
            response_text = (
                "Please select a date for the service (format: YYYY-MM-DD):"
            )
            customer_data[contact_id]["state"] = "select_date"
        elif customer_state == "select_date":
            # Handle date selection
            try:
                selected_date = datetime.datetime.strptime(message_body, "%Y-%m-%d").date()
                customer_data[contact_id]["date"] = selected_date
                
                # Ask for slot selection
                response_text = (
                    "Please select a time slot:\n"
                    "1. 10:00 AM\n"
                    "2. 2:00 PM\n"
                    "3. 4:00 PM\n"
                    "Reply with the number of your choice."
                )
                customer_data[contact_id]["state"] = "select_slot"
            except ValueError:
                response_text = "Invalid date format. Please try again (format: YYYY-MM-DD)."
                send_message(OutgoingMessage(
                    recipient_type="individual",
                    to=contact_id,
                    type="text",
                    text={"body": response_text}
                ))
                continue
        elif customer_state == "select_slot":
            # Handle slot selection
            if message_body == "1":
                customer_data[contact_id]["slot"] = "10:00 AM"
            elif message_body == "2":
                customer_data[contact_id]["slot"] = "2:00 PM"
            elif message_body == "3":
                customer_data[contact_id]["slot"] = "4:00 PM"
            else:
                response_text = "Invalid choice. Please try again."
                send_message(OutgoingMessage(
                    recipient_type="individual",
                    to=contact_id,
                    type="text",
                    text={"body": response_text}
                ))
                continue
            
            # Calculate the price based on the service and date
            selected_service = customer_data[contact_id]["service"]
            base_price = base_prices[selected_service]
            selected_date = customer_data[contact_id]["date"]
            day_of_week = selected_date.strftime("%A")
            
            # Determine price adjustments based on the day of the week
            if day_of_week == discount_day:
                # Apply discount on Saturday
                price = base_price * 0.9  # 10% discount
            elif day_of_week == premium_day:
                # Apply premium on Monday
                price = base_price * 1.1  # 10% premium
            else:
                price = base_price
            
            # Send confirmation message with the final price
            response_text = (
                f"Your appointment details:\n"
                f"Pet: {customer_data[contact_id]['pet']}\n"
                f"Service: {customer_data[contact_id]['service']}\n"
                f"Date: {customer_data[contact_id]['date']}\n"
                f"Time Slot: {customer_data[contact_id]['slot']}\n"
                f"Price: ${price:.2f}\n"
                "Please confirm your appointment (reply 'yes' to confirm)."
            )
            customer_data[contact_id]["state"] = "confirm_appointment"
        
        # Handle appointment confirmation
        elif customer_state == "confirm_appointment":
            if message_body.lower() == "yes":
                # Confirm the appointment
                response_text = "Your appointment has been confirmed! Thank you."
                
                # Reset the customer's state
                customer_data[contact_id]["state"] = "start"
                
                # Clear customer data after the confirmation
                customer_data[contact_id] = {}
            else:
                response_text = "Appointment not confirmed. Please start over."
                # Reset the customer's state
                customer_data[contact_id]["state"] = "start"
        
        # Send the response message to the customer
        send_message(OutgoingMessage(
            recipient_type="individual",
            to=contact_id,
            type="text",
            text={"body": response_text}
        ))
    
    return {"status": "success"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

