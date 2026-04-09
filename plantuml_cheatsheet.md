# PlantUML Guide: Object & Sequence Diagrams

This guide covers the basics of creating Object and Sequence diagrams using PlantUML.

---

## Part 1: Object Diagrams

Object diagrams show *instances* of classes (objects) and their relationships at a specific point in time.

### 1. The Basics: Defining an Object
Every PlantUML diagram starts with `@startuml` and ends with `@enduml`. You define an object using the `object` keyword. 

```plantuml
@startuml
object user1
object "User Admin" as admin
@enduml
```
*Tip: If your object name has spaces, wrap it in quotes and give it an alias using `as` to make the rest of your code cleaner.*

### 2. Adding Attributes (State)
You can add state (attributes and values) using curly braces `{}` or using a colon `:`.

**Method 1: Curly braces (Best for multiple attributes)**
```plantuml
@startuml
object user1 {
  id = 1432
  username = "alice_w"
  status = "Active"
}
@enduml
```

**Method 2: Colon mapping**
```plantuml
@startuml
object user1
user1 : id = 1432
user1 : username = "alice_w"
@enduml
```

### 3. Adding Relationships (Links)
You connect objects using lines. Customize the lines to show different types of relationships:

* `--` (Solid line)
* `..` (Dashed line)
* `-->` (Directional arrow)
* `<--` (Directional arrow, other way)

Add labels by placing a colon `:` after the link:
```plantuml
@startuml
object user
object profile

user --> profile : " owns >"
@enduml
```

### 4. Complete Example (Hair Booking App)
```plantuml
@startuml
' Define the Objects
object "client : User" as client {
  name = "John Doe"
  email = "john@example.com"
}

object "appointment1 : Appointment" as booking {
  date = "2026-04-10"
  time = "14:30"
  status = "Confirmed"
}

object "service1 : Service" as haircut {
  name = "Men's Haircut"
  duration = "45 mins"
  price = "$30"
}

object "staff1 : User" as stylist {
  name = "Sarah"
  role = "Senior Stylist"
}

' Define the relationships
client --> booking : " booked"
booking --> haircut : " includes"
booking --> stylist : " assigned to"
@enduml
```

---

## Part 2: Sequence Diagrams

Sequence diagrams are fantastic for visualizing how different parts of a system interact over time.

### 1. The Basics: Participants and Messages
The most basic syntax is `ParticipantA -> ParticipantB : Message`. PlantUML automatically recognizes names and creates lifelines.

```plantuml
@startuml
User -> Server : Request webpage
Server -> User : Return HTML
@enduml
```

### 2. Defining Participant Types
You can declare participants explicitly to change their shapes:
```plantuml
@startuml
actor User
boundary "Web Interface" as Web
control "Auth Controller" as Auth
database Database

User -> Web : Login(username, password)
Web -> Auth : validate()
Auth -> Database : query_user()
@enduml
```
*Common types:* `actor`, `participant`, `database`, `control`, `boundary`, `queue`, and `collections`. 

### 3. Arrow Styles (Synchronous vs Asynchronous)
The type of arrow communicates the *type* of interaction:
* `->` (Solid line, solid arrow): **Synchronous request** (I ask and wait for a response)
* `-->` (Dotted line, solid arrow): **Return message/Response**
* `->>` (Solid line, open arrow): **Asynchronous request** (I send a message and keep working)

```plantuml
@startuml
Browser -> Server : GET /api/data (Sync)
Server --> Browser : 200 OK JSON (Return)

Browser ->> Analytics : Log event (Async)
@enduml
```

### 4. Activation and Deactivation (Lifelines)
Use `activate` and `deactivate` to show that a system is actively processing a task. (Or use `++` to activate and `--` to deactivate).

```plantuml
@startuml
actor User
participant Server

User -> Server ++ : Fetch Data
Server -> Server : Process Data
note right: Internal processing
Server --> User -- : Result
@enduml
```

### 5. Logic Blocks (Loops, Alt, Opt)
Represent logic inside the diagram:
* **alt / else** (if/else logic)
* **loop** (for/while loops)
* **opt** (optional block)

```plantuml
@startuml
actor User
participant System

User -> System : Place Order

alt Order is Valid
    System --> User : Order Successful
else Invalid Payment
    System --> User : Payment Failed
end

loop Every 5 seconds
    System -> System : Check delivery status
end
@enduml
```

### 6. Complete Example (Booking an Appointment Sequence)

```plantuml
@startuml
autonumber
!theme blueprint

actor Client
participant "Frontend\n(Views)" as View
control "BookingController" as Controller
database "PostgreSQL\nDatabase" as DB

Client -> View ++ : Selects time & clicks booking
View -> Controller ++ : POST /book_appointment

Controller -> DB ++ : Check availability
DB --> Controller -- : Time slot available (True)

alt If Slot Available
    Controller -> DB ++ : Reserve slot & create Appointment
    DB --> Controller -- : Appointment created

    Controller -> Controller : Send Confirmation Email
    Controller --> View : Form Success Re-direct
    View --> Client : Show "Booking Confirmed!"
else If Slot Taken
    Controller --> View : Form Error
    View --> Client : Show "Time Slot Unavailable"
end

deactivate Controller
deactivate View
@enduml
```
