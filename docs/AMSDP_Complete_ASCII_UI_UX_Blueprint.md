# AMSDP — Complete ASCII UI/UX Blueprint
AMSDP — Complete ASCII UI/UX Blueprint
1. Application structure
AMSDP is a multi-tenant, facility-centric application. The interface changes according to the user's role and branch access.
+--------------------------------------------------------------------------+
| AMSDP                                      [Organization] [User] [Logout] |
+----------------------+---------------------------------------------------+
|                      |                                                   |
|  MAIN MENU           |  WORKSPACE                                        |
|                      |                                                   |
|  > Dashboard         |  Page title                                       |
|    Appointments      |  Breadcrumb                                       |
|    Queue             |                                                   |
|    Patients          |  Main content                                     |
|    Doctors           |                                                   |
|    Schedules         |                                                   |
|                      |                                                   |
|  ORGANIZATION        |                                                   |
|    Branches          |                                                   |
|    Staff & Roles     |                                                   |
|                      |                                                   |
|  ADMINISTRATION      |                                                   |
|    Settings          |                                                   |
|    Subscription      |                                                   |
|    Audit Logs        |                                                   |
|                      |                                                   |
+----------------------+---------------------------------------------------+
| Status: Connected | Active Branch: Main Branch | Language: EN / বাংলা      |
+--------------------------------------------------------------------------+

The sidebar should only show modules the current user is authorized to access.
2. Dashboard entity
(Core MVP)
+--------------------------------------------------------------------------+
| DASHBOARD                                     [Branch: Main v] [Today v]  |
+--------------------------------------------------------------------------+
|                                                                          |
|  Today's Appointments    Checked In    In Queue    Completed             |
|       48                    32             12           18                |
|                                                                          |
+--------------------------------------+-----------------------------------+
| APPOINTMENT STATUS                   | TODAY'S QUEUE                     |
|                                      |                                   |
| Booked             10                | #   Patient       Doctor  Status  |
| Confirmed          20                | 01  Rahim Uddin   Dr. A   Waiting |
| Checked In          8                | 02  Salma Akter   Dr. B   Waiting |
| In Queue            5                | 03  Karim Hasan   Dr. A   Called  |
| In Consultation     7                |                                   |
| Completed          18                | [Open Queue]                      |
| Cancelled           2                |                                   |
+--------------------------------------+-----------------------------------+
| QUICK ACTIONS                                                             |
|                                                                          |
| [+ New Appointment] [+ Register Patient] [+ Add Doctor]                 |
|                                                                          |
+--------------------------------------------------------------------------+
| RECENT ACTIVITY                                                          |
| 10:20  Appointment booked         Receptionist A                         |
| 10:15  Patient registered         Receptionist B                         |
| 10:05  Queue position changed     Branch Admin                           |
+--------------------------------------------------------------------------+

Dashboard metrics must be filtered by the user's authorized organization and branch.
3. Organization and branch entities
3.1 Organization management
For Super Admin.
+--------------------------------------------------------------------------+
| ORGANIZATIONS                                      [+ Create Organization]|
+--------------------------------------------------------------------------+
| Search [Organization name / ID................] [Status v] [Search]       |
+--------------------------------------------------------------------------+
| Organization       Organization ID   Branches   Status      Actions      |
|--------------------------------------------------------------------------|
| City Hospital      ORG-0001           3          Active      [View]       |
| Green Clinic       ORG-0002           2          Active      [View]       |
| Care Diagnostic    ORG-0003           1          Suspended   [View]       |
+--------------------------------------------------------------------------+

3.2 Create organization
+--------------------------------------------------------------------------+
| CREATE ORGANIZATION                                                      |
+--------------------------------------------------------------------------+
| Organization Name *       [________________________________]             |
| Organization Type *       [Hospital / Clinic / Diagnostic v]            |
| Contact Person *          [________________________________]             |
| Contact Mobile *          [________________________________]             |
| Email                     [________________________________]             |
| Address                   [________________________________]             |
|                                                                          |
| Subscription Plan         [Plan v]                                       |
| Status                    [Active v]                                     |
|                                                                          |
|                  [Cancel]                 [Create Organization]          |
+--------------------------------------------------------------------------+

3.3 Branch management
+--------------------------------------------------------------------------+
| BRANCHES                                      [+ Add Branch]              |
+--------------------------------------------------------------------------+
| Organization: City Hospital                                              |
| Search [Branch name.................] [Status v] [Search]                 |
+--------------------------------------------------------------------------+
| Branch ID  Branch Name       Location          Status      Actions       |
|--------------------------------------------------------------------------|
| BR-001     Main Branch       Dhaka             Active      [View]        |
| BR-002     Uttara Branch     Uttara            Active      [View]        |
| BR-003     Mirpur Branch     Mirpur            Active      [View]        |
+--------------------------------------------------------------------------+

3.4 Branch details
+--------------------------------------------------------------------------+
| BRANCH DETAILS                                      [Edit]                |
+--------------------------------------------------------------------------+
| Branch Name:       Main Branch                                            |
| Branch ID:         BR-001                                                 |
| Organization:      City Hospital                                         |
| Address:           Dhaka, Bangladesh                                     |
| Contact Mobile:    01XXXXXXXXX                                           |
| Status:            Active                                                |
+--------------------------------------------------------------------------+
| BRANCH OPERATIONS                                                        |
|                                                                          |
| Doctors: 12     Staff: 8     Appointments Today: 48                       |
|                                                                          |
| [Doctors] [Staff] [Schedules] [Appointments] [Queue]                      |
+--------------------------------------------------------------------------+

4. Staff and role entities
The six approved roles:
- Super Admin
- Organization Admin
- Branch Admin
- Receptionist
- Doctor
- Assistant
4.1 Staff list
+--------------------------------------------------------------------------+
| STAFF MANAGEMENT                                     [+ Add Staff]        |
+--------------------------------------------------------------------------+
| Search [Name / Mobile..............] [Role v] [Branch v] [Search]         |
+--------------------------------------------------------------------------+
| Staff ID  Name           Role             Branch       Status  Actions   |
|--------------------------------------------------------------------------|
| STF-001   Admin One      Org Admin        All          Active  [View]    |
| STF-002   Staff Two      Receptionist     Main         Active  [View]    |
| STF-003   Doctor One     Doctor            Main         Active  [View]    |
| STF-004   Staff Four     Assistant         Uttara       Active  [View]    |
+--------------------------------------------------------------------------+

4.2 Create staff
+--------------------------------------------------------------------------+
| CREATE STAFF                                                             |
+--------------------------------------------------------------------------+
| Full Name *              [________________________________]              |
| Mobile Number *          [________________________________]              |
| Email                    [________________________________]              |
| Role *                   [Select Role v]                                 |
|                                                                          |
| Organization *           [Select Organization v]                        |
| Branch Assignment        [Select Branch(es) v]                           |
|                                                                          |
| Login Username *         [________________________________]              |
| Temporary Password *    [________________________________]              |
|                                                                          |
| Account Status           [Active v]                                      |
|                                                                          |
|                  [Cancel]                    [Create Staff]              |
+--------------------------------------------------------------------------+

Role and branch assignment must be validated by the server. Users must not grant themselves higher privileges.
5. Doctor entity
Doctors are facility-local records. A doctor can have different records in different organizations.
5.1 Doctor directory
+--------------------------------------------------------------------------+
| DOCTORS                                           [+ Register Doctor]     |
+--------------------------------------------------------------------------+
| Search [Doctor name / mobile / ID........] [Branch v] [Status v]          |
+--------------------------------------------------------------------------+
| Doctor ID  Doctor Name     Mobile       Specialty    Branch     Actions  |
|--------------------------------------------------------------------------|
| DOC-001    Dr. Rahman      017XXXXXXX   Medicine     Main       [View]   |
| DOC-002    Dr. Akter       018XXXXXXX   Cardiology   Main       [View]   |
| DOC-003    Dr. Hasan       019XXXXXXX   Orthopedic   Uttara     [View]   |
+--------------------------------------------------------------------------+

5.2 Doctor registration
+--------------------------------------------------------------------------+
| REGISTER DOCTOR                                                          |
+--------------------------------------------------------------------------+
| Doctor Name *             [________________________________]             |
| Mobile Number *           [________________________________]             |
| Email                     [________________________________]             |
| Specialty                 [________________________________]             |
| Qualification             [________________________________]             |
| Doctor ID                 [Auto Generated]                               |
|                                                                          |
| Branch Assignment *       [Select Branch v]                              |
| Appointment Model *       ( ) Time Slot                                  |
|                           ( ) Serial Based                               |
|                           ( ) Hybrid                                     |
|                                                                          |
| Status                    [Active v]                                     |
|                                                                          |
|                    [Cancel]                [Save Doctor]                 |
+--------------------------------------------------------------------------+

5.3 Doctor details
+--------------------------------------------------------------------------+
| DOCTOR PROFILE                                     [Edit Doctor]          |
+--------------------------------------------------------------------------+
| Dr. Rahman                                                               |
| DOC-001 | Medicine | Main Branch                                         |
| Mobile: 017XXXXXXX                                                       |
+--------------------------------------------------------------------------+
| [Overview] [Schedules] [Appointments] [Queue]                            |
+--------------------------------------------------------------------------+
| Today's Appointments: 18                                                 |
| Completed: 12                                                            |
| Waiting: 4                                                               |
| Cancelled: 2                                                             |
|                                                                          |
| [Create Schedule] [View Today's Queue]                                   |
+--------------------------------------------------------------------------+

6. Patient entity
Patients do not need AMSDP login accounts. Reception staff register and manage their records.

Multiple patients within the same organization may share a mobile number.
6.1 Patient directory
+--------------------------------------------------------------------------+
| PATIENTS                                           [+ Register Patient]   |
+--------------------------------------------------------------------------+
| Search [Patient ID / Name / Mobile...................] [Search]           |
+--------------------------------------------------------------------------+
| Patient ID  Patient Name   Mobile        Age   Gender   Actions          |
|--------------------------------------------------------------------------|
| PAT-001     Rahim Uddin    017XXXXXXX    42    Male     [View]           |
| PAT-002     Salma Akter    018XXXXXXX    35    Female   [View]           |
| PAT-003     Karim Hasan    017XXXXXXX    12    Male     [View]           |
+--------------------------------------------------------------------------+

6.2 Patient registration
+--------------------------------------------------------------------------+
| REGISTER PATIENT                                                         |
+--------------------------------------------------------------------------+
| Patient Name *           [________________________________]             |
| Mobile Number *          [________________________________]             |
| Date of Birth            [____ / ____ / ______]                          |
| Gender                   [Select v]                                      |
| Address                  [________________________________]             |
|                                                                          |
| Additional Information                                                   |
| Notes                    [________________________________]             |
|                                                                          |
|                         [Cancel]       [Register Patient]               |
+--------------------------------------------------------------------------+

6.3 Possible duplicate warning
+--------------------------------------------------------------------------+
|                    POSSIBLE EXISTING PATIENT                             |
+--------------------------------------------------------------------------+
| A patient with a similar name or mobile number was found.                |
|                                                                          |
| Existing Patient                                                         |
| PAT-001 | Rahim Uddin | 017XXXXXXX                                       |
|                                                                          |
| [Open Existing Record]     [Register as New Patient]                     |
+--------------------------------------------------------------------------+

No automatic merging. Staff must decide whether this is an existing or new patient.
6.4 Patient details
+--------------------------------------------------------------------------+
| PATIENT PROFILE                                     [Edit Patient]        |
+--------------------------------------------------------------------------+
| PAT-001                                                                  |
| Rahim Uddin                                                              |
| Mobile: 017XXXXXXX                                                       |
| Age: 42                                                                  |
+--------------------------------------------------------------------------+
| [Overview] [Appointments] [Activity History]                             |
+--------------------------------------------------------------------------+
| APPOINTMENT HISTORY                                                      |
|                                                                          |
| Date        Doctor        Branch      Status                             |
| 06 Nov      Dr. Rahman    Main        Completed                          |
| 01 Nov      Dr. Akter     Main        Cancelled                          |
| 20 Oct      Dr. Rahman    Uttara      Completed                          |
|                                                                          |
|                        [+ Book Appointment]                              |
+--------------------------------------------------------------------------+

This is scheduling history, not a clinical record or EMR.
7. Doctor schedule entity
7.1 Schedule list
+--------------------------------------------------------------------------+
| DOCTOR SCHEDULES                                      [+ Create Schedule] |
+--------------------------------------------------------------------------+
| Doctor [All v]   Branch [All v]   Day [All v]   [Search]                 |
+--------------------------------------------------------------------------+
| Doctor       Day        Start       End         Model       Actions      |
|--------------------------------------------------------------------------|
| Dr. Rahman   Saturday   16:00       20:00       Time Slot   [Edit]       |
| Dr. Rahman   Monday     16:00       20:00       Time Slot   [Edit]       |
| Dr. Akter    Sunday     17:00       21:00       Serial      [Edit]       |
+--------------------------------------------------------------------------+

7.2 Create schedule
+--------------------------------------------------------------------------+
| CREATE DOCTOR SCHEDULE                                                   |
+--------------------------------------------------------------------------+
| Doctor *                 [Select Doctor v]                               |
| Branch *                 [Select Branch v]                               |
|                                                                          |
| Schedule Type            [Recurring / Specific Date v]                   |
| Day                      [Saturday v]                                    |
| Effective From           [Date Picker]                                   |
| Effective Until          [Date Picker]                                   |
|                                                                          |
| Start Time *             [04:00 PM]                                      |
| End Time *               [08:00 PM]                                      |
|                                                                          |
| Appointment Model *      ( ) Time Slot                                   |
|                          ( ) Serial Based                                |
|                          ( ) Hybrid                                      |
|                                                                          |
| Slot Duration            [15 / 30 minutes v]                             |
| Capacity                 [________]                                      |
|                                                                          |
|                     [Cancel]            [Save Schedule]                 |
+--------------------------------------------------------------------------+

7.3 Schedule calendar
+--------------------------------------------------------------------------+
| WEEKLY SCHEDULE — DR. RAHMAN                                             |
+--------------------------------------------------------------------------+
|       SAT       SUN       MON       TUE       WED       THU       FRI     |
|--------------------------------------------------------------------------|
| AM    -         -         -         -         -         -         -      |
|                                                                          |
| PM    4-8 PM    -         4-8 PM    -         4-8 PM    -         -      |
|                                                                          |
+--------------------------------------------------------------------------+
| [Edit Schedule] [Block Time] [View Appointments]                          |
+--------------------------------------------------------------------------+

Blocking time should not silently modify already-booked appointment times.
8. Appointment entity
This is the central operational entity connecting patient, doctor, branch, schedule, and queue.
8.1 Appointment directory
+--------------------------------------------------------------------------+
| APPOINTMENTS                                      [+ New Appointment]     |
+--------------------------------------------------------------------------+
| Date [Today v] Doctor [All v] Branch [All v] Status [All v] [Search]     |
+--------------------------------------------------------------------------+
| Booking ID  Patient       Doctor       Time      Status       Actions    |
|--------------------------------------------------------------------------|
| APT-001     Rahim Uddin   Dr. Rahman   04:00 PM  Confirmed    [View]     |
| APT-002     Salma Akter   Dr. Akter    04:15 PM  Booked       [View]     |
| APT-003     Karim Hasan   Dr. Rahman   04:30 PM  Checked In   [View]     |
+--------------------------------------------------------------------------+

8.2 New appointment — step 1: Patient
+--------------------------------------------------------------------------+
| NEW APPOINTMENT                                      STEP 1 OF 4         |
+--------------------------------------------------------------------------+
|                                                                          |
| Patient                                                                  |
|                                                                          |
| Search Existing Patient [Name / Mobile / Patient ID........] [Search]    |
|                                                                          |
| OR                                                                       |
|                                                                          |
| [+ Register New Patient]                                                 |
|                                                                          |
| Selected Patient:                                                       |
| PAT-001 | Rahim Uddin | 017XXXXXXX                                       |
|                                                                          |
|                                         [Next: Doctor & Branch >]        |
+--------------------------------------------------------------------------+

8.3 New appointment — step 2: Doctor and branch
+--------------------------------------------------------------------------+
| NEW APPOINTMENT                                      STEP 2 OF 4         |
+--------------------------------------------------------------------------+
| Organization             City Hospital                                   |
| Branch *                 [Main Branch v]                                |
| Doctor *                 [Dr. Rahman v]                                  |
|                                                                          |
| Appointment Date *       [06 Nov 2026]                                   |
| Appointment Model        [Time Slot v]                                  |
|                                                                          |
| Available Time Slots                                                     |
|                                                                          |
| [04:00 PM] [04:15 PM] [04:30 PM] [04:45 PM]                              |
| [05:00 PM] [05:15 PM] [05:30 PM] [05:45 PM]                              |
|                                                                          |
|                                      [< Back] [Next: Review >]           |
+--------------------------------------------------------------------------+

For serial-based schedules, the interface should offer the relevant serial booking flow instead of time slots.
8.4 New appointment — step 3: Review
+--------------------------------------------------------------------------+
| NEW APPOINTMENT                                      STEP 3 OF 4         |
+--------------------------------------------------------------------------+
| Patient:          Rahim Uddin                                            |
| Doctor:           Dr. Rahman                                             |
| Branch:           Main Branch                                            |
| Date:             06 Nov 2026                                            |
| Time:             04:15 PM                                               |
|                                                                          |
| Booking Source:   Staff Booking                                          |
|                                                                          |
| Notes (optional)  [________________________________________]             |
|                                                                          |
| Appointment Status: [Booked v]                                           |
|                                                                          |
|                         [< Back] [Create Appointment]                    |
+--------------------------------------------------------------------------+

8.5 Appointment details
+--------------------------------------------------------------------------+
| APPOINTMENT DETAILS                                  APT-001             |
+--------------------------------------------------------------------------+
| Patient:          Rahim Uddin                                            |
| Doctor:           Dr. Rahman                                             |
| Branch:           Main Branch                                            |
| Date:             06 Nov 2026                                            |
| Appointment Time: 04:00 PM                                               |
| Queue Position:   03                                                     |
| Status:           CONFIRMED                                              |
+--------------------------------------------------------------------------+
| ACTIONS                                                                  |
| [Check In] [Reschedule] [Cancel] [View Queue]                            |
+--------------------------------------------------------------------------+
| STATUS HISTORY                                                           |
| 03:00 PM  Booked            Receptionist A                               |
| 03:10 PM  Confirmed         Receptionist A                               |
|                                                                          |
+--------------------------------------------------------------------------+

Rescheduling preserves the original appointment and creates a linked new appointment.
9. Queue entity
(Critical operational screen)
9.1 Live queue board
+--------------------------------------------------------------------------+
| LIVE QUEUE                                      [Main Branch v] [Refresh]|
+--------------------------------------------------------------------------+
| Doctor: Dr. Rahman          Date: 06 Nov 2026                             |
|                                                                          |
| Waiting: 08    In Consultation: 01    Completed: 05                      |
+--------------------------------------------------------------------------+
| POS | PATIENT       | TOKEN | APPOINTMENT | STATUS          | ACTIONS    |
|--------------------------------------------------------------------------|
|  01 | Rahim Uddin   |  01   | 04:00 PM    | Waiting         | [Call]     |
|  02 | Salma Akter   |  02   | 04:15 PM    | Waiting         | [Call]     |
|  03 | Karim Hasan   |  03   | 04:30 PM    | Waiting         | [Call]     |
|  04 | Nadia Islam   |  04   | 04:45 PM    | In Consultation| [Complete]|
|  05 | Hasan Ali     |  05   | 05:00 PM    | Skipped         | [Next]     |
+--------------------------------------------------------------------------+
| QUEUE CONTROLS                                                           |
|                                                                          |
| [Move Up] [Move Down] [Skip] [Call Next] [Complete]                     |
|                                                                          |
| Queue order changes must be recorded in the audit history.              |
+--------------------------------------------------------------------------+

9.2 Queue item details
+--------------------------------------------------------------------------+
| QUEUE ITEM DETAILS                                                       |
+--------------------------------------------------------------------------+
| Patient:            Rahim Uddin                                          |
| Appointment:        APT-001                                              |
| Token:              01                                                   |
| Current Position:   03                                                   |
| Appointment Time:   04:00 PM                                             |
| Status:             Waiting                                              |
|                                                                          |
| [Move to Position...]                                                    |
| [Mark Skipped]                                                           |
| [Call Patient]                                                           |
| [Mark In Consultation]                                                   |
| [Mark Completed]                                                         |
|                                                                          |
| Queue History                                                            |
| 03:00 PM Position 01 created                                             |
| 03:10 PM Moved from 01 to 03                                             |
+--------------------------------------------------------------------------+

The system must keep appointment time and queue position separate. Estimated waiting times are indicative, not guaranteed.
10. Appointment and queue lifecycle
                 +----------------+
                 |     BOOKED     |
                 +----------------+
                         |
              +----------+----------+
              |                     |
              v                     v
      +----------------+   +----------------------+
      |   CONFIRMED    |   | AWAITING_CONFIRMATION|
      +----------------+   +----------------------+
              |                     |
              +----------+----------+
                         |
                         v
                 +----------------+
                 |  CHECKED_IN    |
                 +----------------+
                         |
                         v
                 +----------------+
                 |   IN_QUEUE     |
                 +----------------+
                         |
                         v
                 +----------------+
                 | IN_CONSULTATION|
                 +----------------+
                         |
                         v
                 +----------------+
                 |   COMPLETED    |
                 +----------------+

  Other permitted transitions:
  BOOKED / CONFIRMED -> CANCELLED
  BOOKED / CONFIRMED -> NO_SHOW (staff-confirmed)
  Existing appointment -> RESCHEDULED (linked replacement appointment)

11. Organization settings and configuration
+--------------------------------------------------------------------------+
| ORGANIZATION SETTINGS                                                    |
+--------------------------------------------------------------------------+
| [General] [Appointment] [Queue] [Cancellation] [Capacity] [Permissions] |
+--------------------------------------------------------------------------+
| GENERAL SETTINGS                                                         |
|                                                                          |
| Organization Name      [City Hospital_____________]                      |
| Default Language       [English v]                                       |
| Time Zone              [Asia/Dhaka v]                                    |
|                                                                          |
| APPOINTMENT SETTINGS                                                     |
| Default Model          [Time Slot v]                                     |
| Default Slot Duration  [15 minutes v]                                    |
| Allow Overbooking      [ ] Disabled                                      |
|                                                                          |
| QUEUE SETTINGS                                                           |
| Queue Management       [Manual Reorder v]                                |
| Walk-in Policy         [End of Queue v]                                  |
|                                                                          |
| CANCELLATION SETTINGS                                                    |
| Cancellation Enabled   [✓]                                               |
| Require Reason         [✓]                                               |
|                                                                          |
| NO-SHOW SETTINGS                                                         |
| Grace Period           [15 minutes]                                      |
| Staff Confirmation     [✓] Required                                      |
|                                                                          |
|                         [Cancel] [Save Settings]                         |
+--------------------------------------------------------------------------+

Super Admin controls system-wide limits and permitted options; organizations configure their settings within those limits.
12. Subscription entity
+--------------------------------------------------------------------------+
| SUBSCRIPTION MANAGEMENT                                                  |
+--------------------------------------------------------------------------+
| Organization: City Hospital                                              |
| Current Plan: Professional                                               |
| Status: Active                                                           |
|                                                                          |
| Start Date: 01 Nov 2026                                                  |
| Renewal Date: 01 Dec 2026                                                |
|                                                                          |
| FEATURES / LIMITS                                                        |
| Branch Limit:             5                                              |
| Staff Limit:              30                                             |
| Doctor Limit:             50                                             |
|                                                                          |
| [Change Plan] [View Subscription History]                                |
+--------------------------------------------------------------------------+

Expiry behavior:
ACTIVE
  |
  v
EXPIRED
  |
  v
GRACE PERIOD
  |
  v
READ-ONLY ACCESS

Existing data is retained. No automatic deletion.

13. Audit log entity
+--------------------------------------------------------------------------+
| AUDIT LOGS                                                               |
+--------------------------------------------------------------------------+
| Date [From / To] User [All v] Action [All v] Entity [All v] [Search]     |
+--------------------------------------------------------------------------+
| TIME       USER         ACTION             ENTITY       DETAILS          |
|--------------------------------------------------------------------------|
| 10:20 AM   Staff A      Created            Appointment  APT-001          |
| 10:15 AM   Admin B      Updated            Patient      PAT-002          |
| 10:10 AM   Staff C      Queue Reorder      Queue        01 -> 03         |
| 10:05 AM   Admin B      Changed Settings   Organization Cancellation    |
+--------------------------------------------------------------------------+
| [View Event Details]                                                     |
+--------------------------------------------------------------------------+

Audit event detail
+--------------------------------------------------------------------------+
| AUDIT EVENT DETAILS                                                      |
+--------------------------------------------------------------------------+
| Event ID:       EVT-0001                                                 |
| Actor:          Staff A                                                  |
| Action:         Queue Position Changed                                   |
| Entity:         APT-001                                                  |
| Timestamp:      06 Nov 2026 10:10 AM                                     |
|                                                                          |
| Previous Position: 01                                                   |
| New Position:      03                                                   |
| Reason:            Staff adjustment                                     |
|                                                                          |
| [Close]                                                                  |
+--------------------------------------------------------------------------+

14. Public landing page and login
14.1 Public landing page
+--------------------------------------------------------------------------+
| AMSDP                                  Features   About   Contact  Login |
+--------------------------------------------------------------------------+
|                                                                          |
|           SIMPLER APPOINTMENT MANAGEMENT                                 |
|           FOR HEALTHCARE FACILITIES                                      |
|                                                                          |
|           Manage doctors, patients, appointments                         |
|           and daily queues in one place.                                 |
|                                                                          |
|           [Staff Login]                                                  |
|                                                                          |
+--------------------------------------------------------------------------+
|                                                                          |
|       DOCTOR MANAGEMENT       APPOINTMENT SCHEDULING                     |
|       PATIENT RECORDS         QUEUE MANAGEMENT                           |
|       MULTI-BRANCH SUPPORT    ROLE-BASED ACCESS                           |
|                                                                          |
+--------------------------------------------------------------------------+
| About AMSDP | Contact | Privacy | Terms                                  |
+--------------------------------------------------------------------------+

14.2 Staff login
+--------------------------------------------------------------+
|                                                              |
|                         AMSDP                                |
|                                                              |
|                  STAFF LOGIN                                 |
|                                                              |
|             Username / Mobile                                |
|             [________________________]                       |
|                                                              |
|             Password                                         |
|             [________________________]                       |
|                                                              |
|             [✓] Remember me                                  |
|                                                              |
|                    [ SIGN IN ]                               |
|                                                              |
|             Forgot password?                                 |
|                                                              |
+--------------------------------------------------------------+

No patient login or patient self-booking interface.
15. Public Daily Queue Display (DQDS)
This is an optional Phase 2 feature, not a requirement for the core MVP.
+--------------------------------------------------------------------------+
|                         CITY HOSPITAL                                    |
|                         MAIN BRANCH                                      |
+--------------------------------------------------------------------------+
|                                                                          |
|                         DR. RAHMAN                                      |
|                                                                          |
|                       NOW SERVING                                       |
|                                                                          |
|                            03                                            |
|                                                                          |
|                       NEXT TOKENS                                        |
|                                                                          |
|                  04       05       06                                    |
|                                                                          |
|                 Please wait for your turn                               |
|                                                                          |
+--------------------------------------------------------------------------+

No patient mobile numbers or other personal information should be displayed.
16. Complete entity and screen inventory
This is the screen coverage I recommend using as the frontend delivery checklist.
Entity / module	List	Create	Detail	Edit	Operational actions
Organization	✓	✓	✓	✓	Activate / suspend
Branch	✓	✓	✓	✓	Activate / deactivate
Staff / User	✓	✓	✓	✓	Assign role / branch
Role / Permissions	✓	—	✓	✓	Configure access
Doctor	✓	✓	✓	✓	Activate / deactivate
Patient	✓	✓	✓	✓	Duplicate warning
Doctor Schedule	✓	✓	✓	✓	Block time
Appointment	✓	✓	✓	✓	Check-in / cancel / reschedule
Queue Entry	✓	—	✓	—	Reorder / skip / call / complete
Organization Settings	—	—	✓	✓	Configure policies
Subscription	✓	✓	✓	✓	Plan / expiry management
Audit Log	✓	—	✓	—	Inspect event
DQDS	—	—	✓	—	Display queue


Role/permission management is part of staff access administration; it should not become an uncontrolled custom-role system unless that is separately approved.
17. Recommended application navigation by role
Module	Super Admin	Org Admin	Branch Admin	Receptionist	Doctor	Assistant
Organizations	✓	—	—	—	—	—
Branches	✓	✓	Assigned	—	—	—
Staff	✓	✓	Assigned	—	—	—
Doctors	✓	✓	✓	View	View	View
Patients	—	✓	✓	✓	Permission-based	Permission-based
Schedules	—	✓	✓	View	View own	View assigned
Appointments	—	✓	✓	✓	Own	Assigned
Queue	—	✓	✓	✓	Own	Assigned
Settings	✓	✓	Limited	—	—	—
Subscription	✓	✓	—	—	—	—
Audit Logs	✓	✓	Scoped	—	—	—


These are proposed screen-access defaults and should be reconciled with the approved permission matrix before implementation.
18. Recommended UI development order
To make AMSDP demonstrable as an actual working product—not merely a collection of attractive screens—I recommend this sequence:
1. Application shell and authentication
   Sidebar, header, login, role-based navigation, branch selector.
2. Organization, branch and staff management
   Tenant creation, branch assignment, roles, permissions.
3. Doctors and patients
   Complete CRUD, search, duplicate warnings, profile details.
4. Schedules
   Create, edit, block time, configure appointment models and capacity.
5. Appointments
   Complete staff-mediated booking, confirmation, cancellation and rescheduling.
6. Queue management
   Check-in, serial assignment, reorder, skip, call and completion.
7. Settings, subscription and audit
   Complete administrative workflows and access controls.
8. Dashboard and public landing page
   Live operational metrics and a polished public-facing introduction.
My main recommendation: treat the ASCII screens above as the UI/UX baseline for AILI's Frontend Developer agent. Require every screen to have working API integration, validation, loading states, empty states, error states, and permission checks. A button that looks functional but has no working operation should not count as a completed feature.

This blueprint follows the approved AMSDP scope and entity rules.

1. Main floor display — TV / LED screen
(Recommended public display UI)
+----------------------------------------------------------------------------------+
|                           CITY HOSPITAL                                          |
|                    DOCTOR CHAMBER & TOKEN DISPLAY                                |
|                                                                                  |
|  Building: Main Building       Floor: 3rd Floor        Date: 06 NOV 2026         |
|----------------------------------------------------------------------------------|
|                                                                                  |
|  ROOM 301                 ROOM 302                 ROOM 303                      |
|  DR. RAHMAN               DR. AKTER                DR. HASAN                     |
|  Medicine                 Cardiology               Orthopedic                    |
|                                                                                  |
|  NOW SERVING              NOW SERVING              NOW SERVING                   |
|                                                                                  |
|      012                      025                      008                        |
|                                                                                  |
|  NEXT TOKENS              NEXT TOKENS              NEXT TOKENS                   |
|                                                                                  |
|   013  014  015            026  027  028            009  010  011                |
|                                                                                  |
|  STATUS: SERVING          STATUS: SERVING          STATUS: DELAYED               |
|----------------------------------------------------------------------------------|
|                                                                                  |
|  ROOM 304                 ROOM 305                 ROOM 306                      |
|  DR. ISLAM                DR. SULTANA              DR. KARIM                    |
|  Dermatology              Gynecology               Pediatrics                    |
|                                                                                  |
|  NOW SERVING              NOW SERVING              NOW SERVING                   |
|                                                                                  |
|      005                      018                      031                        |
|                                                                                  |
|  NEXT TOKENS              NEXT TOKENS              NEXT TOKENS                   |
|                                                                                  |
|   006  007  008            019  020  021            032  033  034                |
|                                                                                  |
|  STATUS: SERVING          STATUS: BREAK            STATUS: SERVING               |
|----------------------------------------------------------------------------------|
|                                                                          05:42 PM |
|       PLEASE WAIT FOR YOUR TOKEN. DO NOT ENTER THE CHAMBER UNTIL CALLED.         |
|       আপনার টোকেন নম্বর প্রদর্শিত হলে নির্দিষ্ট কক্ষে প্রবেশ করুন।                |
+----------------------------------------------------------------------------------+

This is the main concept: one screen, multiple rooms, all doctors, individual token queues.
2. More polished layout for a large display
For a 16:9 television or LED display, I recommend a grid of doctor cards.
CITY HOSPITAL
(LIVE QUEUE)
DOCTOR CHAMBER DISPLAY
MAIN BUILDING · 3RD FLOOR 06 NOV 2026 · 05:42 PM
আপনার টোকেন নম্বর প্রদর্শিত হলে নির্দিষ্ট কক্ষে প্রবেশ করুন।
Please enter the chamber only when your token is called.

This is a layout illustration. Actual display cards should be optimized for viewing from a distance, with large token numbers and high contrast.
3. Individual doctor queue display
Each room should also be able to have its own smaller screen outside the chamber.
+------------------------------------------------------+
|                    CITY HOSPITAL                     |
|                    ROOM 301                          |
|------------------------------------------------------|
|                                                      |
|                    DR. RAHMAN                        |
|                      MEDICINE                        |
|                                                      |
|                  NOW SERVING                         |
|                                                      |
|                       012                            |
|                                                      |
|------------------------------------------------------|
|                  NEXT TOKENS                         |
|                                                      |
|                013     014     015                   |
|                                                      |
|------------------------------------------------------|
|  STATUS: SERVING                                     |
|                                                      |
|  আপনার টোকেন নম্বরের জন্য অপেক্ষা করুন।              |
+------------------------------------------------------+

4. Staff control panel — manage all rooms
The public screen must be driven by a staff-facing control panel. Assistants should not need to edit the TV display manually.
+--------------------------------------------------------------------------------+
| AMSDP — FLOOR QUEUE CONTROL                                                   |
+--------------------------------------------------------------------------------+
| Organization: City Hospital    Branch: Main    Floor: 3rd Floor               |
+--------------------------------------------------------------------------------+
| ROOM | DOCTOR       | NOW SERVING | NEXT | STATUS       | ACTIONS              |
|--------------------------------------------------------------------------------|
| 301  | Dr. Rahman   | 012         | 013  | Serving      | [Call Next]          |
| 302  | Dr. Akter    | 025         | 026  | Serving      | [Call Next]          |
| 303  | Dr. Hasan    | 008         | 009  | Delayed      | [Update Status]      |
| 304  | Dr. Islam    | 005         | 006  | Serving      | [Call Next]          |
| 305  | Dr. Sultana  | 018         | ---  | On Break     | [Resume]             |
| 306  | Dr. Karim    | 031         | 032  | Serving      | [Call Next]          |
+--------------------------------------------------------------------------------+
| SELECTED ROOM: 301                                                           |
|                                                                                |
| [Call Next Patient] [Skip] [Repeat Call] [Complete Consultation]              |
| [Pause Queue] [Resume Queue] [Change Room]                                     |
+--------------------------------------------------------------------------------+

A call-next action should advance the queue through the approved appointment and queue state transitions. It must not silently change appointment times.
5. New entity: Room / Chamber
This introduces an important concept into the AMSDP data model.

A doctor is assigned to a room for a particular branch and operational session. A room is not the same thing as a doctor or a branch.
ORGANIZATION
    |
    +-- BRANCH
          |
          +-- FLOOR
                |
                +-- ROOM 301
                |     |
                |     +-- DOCTOR: Dr. Rahman
                |     +-- ACTIVE SESSION
                |     +-- QUEUE
                |
                +-- ROOM 302
                |     |
                |     +-- DOCTOR: Dr. Akter
                |     +-- ACTIVE SESSION
                |     +-- QUEUE
                |
                +-- ROOM 303
                      |
                      +-- DOCTOR: Dr. Hasan
                      +-- ACTIVE SESSION
                      +-- QUEUE

Suggested entity fields:
Entity	Important fields
Floor	Floor ID, branch ID, floor name
Room	Room ID, floor ID, room number/name, status
Doctor-room assignment	Doctor ID, room ID, effective session, assignment status
Floor display	Floor ID, display name, display configuration
Queue	Appointment ID, doctor/session, room assignment, token, queue position


Room assignments need effective dates/times and history. A doctor may work in different rooms at different sessions.
6. Important operational rules
I recommend these rules for the Bangladesh hospital environment:
1. One floor, one consolidated screen: Display all active doctors and rooms on the selected floor.
2. One queue per doctor/session: Each doctor's token sequence is independent.
3. Room-based visibility: The public screen shows room number prominently.
4. No patient names: Public screens show tokens, not personal information.
5. Live updates: Calling the next token updates the floor screen automatically.
6. Break and delay status: A doctor can be marked on break, delayed, or unavailable.
7. Room reassignment: Authorized staff can move a doctor to another room while preserving queue history and updating the public display.
8. Multiple display support: A facility may have one floor display and multiple chamber displays.
9. Bangla and English: Both should be supported, with Bangla instructions available.
10. Connection failure: Show a visible last-updated/connection warning rather than displaying misleading stale queue information.
7. Where this fits in AMSDP
This should become a formal part of the approved product blueprint:
Feature	Priority
Floor management	P0
Room/chamber management	P0
Doctor-room session assignment	P0
Multi-doctor floor display	P0
Room-specific token display	P1
Floor queue control panel	P0
Public display connection monitoring	P1


One important design decision: I recommend making the floor display a separate, read-only public interface, while all queue operations remain inside the authenticated AMSDP staff dashboard. This keeps patient-facing displays simple and protects operational controls.

1. Additional UI screens I recommend
(P0 — Complete before development)
Screen	Why it is needed
Floor management	Create and manage floors within a branch
Room/chamber management	Create rooms and assign room numbers
Doctor-room assignment	Assign doctors to rooms for specific sessions
Walk-in registration	Register patients arriving without prior appointments
Walk-in policy configuration	Manage FCFS, end-of-queue and reserved capacity
Appointment rescheduling	Dedicated workflow preserving original appointment history
Cancellation and no-show management	Reason capture and staff confirmation
Queue history	Review token movements, skipped patients and completed consultations
Branch switching	Let authorized staff switch between assigned branches
Permission management	Clearly configure what each staff role can do


2. Additional operational screens
(P1 — Strongly recommended)
Screen	Purpose
Room availability board	See occupied, available and temporarily blocked rooms
Doctor availability board	See which doctors are working today
Schedule conflict screen	Identify overlapping schedules and capacity conflicts
Appointment search	Quickly locate a booking by ID, patient or mobile
Patient duplicate resolution	Help authorized staff correct duplicate records
Audit event detail	Inspect who changed what and why
Subscription read-only screen	Explain expired subscription restrictions
Display management	Configure public floor and chamber displays


3. Three particularly important workflows
These deserve dedicated wireframes because they involve multiple entities.

A. Walk-in patient workflow
Reception
   |
   v
Search existing patient
   |
   +---- Found ----> Select patient
   |
   +---- Not found -> Register patient
                         |
                         v
                  Select doctor
                         |
                         v
                  Check capacity
                         |
                         v
                  Create walk-in
                         |
                         v
                  Assign queue position
                         |
                         v
                  Show token / receipt

B. Doctor changes room
Doctor currently in Room 301
             |
             v
Authorized staff selects
"Change Room"
             |
             v
Select Room 305
             |
             v
Check room availability
             |
             v
Confirm reassignment
             |
             v
Update floor display
             |
             v
Preserve queue and assignment history

C. Doctor finishes a session
Doctor session active
       |
       v
Stop accepting new bookings
       |
       v
Check remaining queue
       |
       +---- Pending patients?
       |          |
       |          v
       |    Staff resolves queue
       |
       v
Close session
       |
       v
Preserve appointment and queue history

4. One important screen: Today's Operations Overview
I would add this to the branch administrator's dashboard.
+--------------------------------------------------------------------------+
| TODAY'S BRANCH OPERATIONS                     MAIN BRANCH | 06 NOV       |
+--------------------------------------------------------------------------+
| DOCTORS WORKING | ROOMS ACTIVE | APPOINTMENTS | WALK-INS | WAITING       |
|       12        |      10      |      86      |    14    |    23         |
+--------------------------------------------------------------------------+
| DOCTOR / ROOM STATUS                                                     |
|                                                                          |
| Dr. Rahman     Room 301    Serving       Token 012                       |
| Dr. Akter      Room 302    Serving       Token 025                       |
| Dr. Hasan      Room 303    Delayed       Token 008                       |
| Dr. Islam      Room 304    Available     No active token                 |
| Dr. Sultana    Room 305    On Break      Token 018                       |
+--------------------------------------------------------------------------+
| OPERATIONAL ALERTS                                                       |
|                                                                          |
| ! Room 303 has a delayed queue                                           |
| ! Room 306 has reached configured capacity                               |
| ! Dr. Karim's session ends in 30 minutes                                 |
+--------------------------------------------------------------------------+

5. Final UI/UX coverage checklist
Blueprint coverage
/
[Reset checklist]
My recommendation
I would now freeze the core UI/UX scope after designing the additional screens above.

Then we should produce three deliverables:
1. Complete ASCII wireframe specification — every screen, form, table, dialog and state.
2. Navigation and role-permission map — what each of the six roles can see and operate.
3. Entity-to-screen/API mapping — every UI action connected to its backend operation.
One important boundary: keep the optional public digital queue display and printed token enhancements separate from the core MVP unless we explicitly promote them.

I recommend we design the missing P0 screens next, starting with Floor, Room, Doctor-Room Assignment and Walk-in Registration. These complete the physical hospital workflow that connects reception, doctors, chambers and patients.













design rest of the UIs












I'll complete the remaining AMSDP screens, using the same ASCII wireframe style. These designs extend the existing blueprint and cover the workflows we haven't drawn yet: facility layout, rooms, doctor assignments, walk-ins, appointment exceptions, display configuration, and administrative operations.

The designs follow the approved AMSDP rules: organization and branch isolation, staff-mediated patient registration, configurable scheduling, independent doctor queues, and auditable changes.
AMSDP — Remaining UI/UX Wireframes
1. Floor management
Purpose: Allow an organization administrator or authorized branch administrator to create and manage floors within a branch.
1.1 Floor directory
+--------------------------------------------------------------------------+
| FLOOR MANAGEMENT                                      [+ Add Floor]      |
+--------------------------------------------------------------------------+
| Organization: City Hospital     Branch: Main Branch                      |
+--------------------------------------------------------------------------+
| Search [Floor name / code................] [Status v] [Search]            |
+--------------------------------------------------------------------------+
| FLOOR ID | FLOOR NAME   | ROOMS | DOCTORS TODAY | STATUS  | ACTIONS       |
|----------|--------------|-------|---------------|---------|---------------|
| FL-001   | Ground Floor | 8     | 5             | Active  | [View] [Edit] |
| FL-002   | 1st Floor    | 6     | 4             | Active  | [View] [Edit] |
| FL-003   | 2nd Floor    | 10    | 7             | Active  | [View] [Edit] |
| FL-004   | 3rd Floor    | 8     | 6             | Active  | [View] [Edit] |
+--------------------------------------------------------------------------+

1.2 Add floor
+--------------------------------------------------------------------------+
| CREATE FLOOR                                                             |
+--------------------------------------------------------------------------+
| Organization *       City Hospital                                      |
| Branch *             [Main Branch v]                                    |
|                                                                          |
| Floor Name *         [3rd Floor____________________]                     |
| Floor Code           [FL-003_______________________]                     |
| Floor Description    [_____________________________]                     |
|                                                                          |
| Status               [Active v]                                         |
|                                                                          |
|                       [Cancel] [Create Floor]                            |
+--------------------------------------------------------------------------+

1.3 Floor details
+--------------------------------------------------------------------------+
| FLOOR: 3RD FLOOR                                      [Edit Floor]       |
+--------------------------------------------------------------------------+
| Branch: Main Branch                                                     |
| Rooms: 8             Active Doctors Today: 6                            |
| Active Displays: 1                                                      |
+--------------------------------------------------------------------------+
| [Overview] [Rooms] [Doctor Assignments] [Displays] [Queue]              |
+--------------------------------------------------------------------------+
| ROOM      | DOCTOR          | CURRENT TOKEN | STATUS                    |
|-----------|-----------------|---------------|---------------------------|
| 301       | Dr. Rahman      | 012           | Serving                   |
| 302       | Dr. Akter       | 025           | Serving                   |
| 303       | Dr. Hasan       | 008           | Delayed                   |
| 304       | Dr. Islam       | --            | Available                 |
+--------------------------------------------------------------------------+
| [+ Add Room] [Assign Doctor] [Configure Floor Display]                   |
+--------------------------------------------------------------------------+

2. Room / chamber management
2.1 Room directory
+--------------------------------------------------------------------------+
| ROOM MANAGEMENT                                        [+ Add Room]      |
+--------------------------------------------------------------------------+
| Branch [Main v]  Floor [All v]  Status [All v]  [Search]                 |
+--------------------------------------------------------------------------+
| ROOM ID | ROOM NO. | FLOOR       | CURRENT DOCTOR | STATUS   | ACTIONS   |
|---------|----------|-------------|----------------|----------|-----------|
| RM-001  | 301      | 3rd Floor   | Dr. Rahman     | Active   | [View]   |
| RM-002  | 302      | 3rd Floor   | Dr. Akter      | Active   | [View]   |
| RM-003  | 303      | 3rd Floor   | Dr. Hasan      | Active   | [View]   |
| RM-004  | 401      | 4th Floor   | --             | Available| [View]  |
+--------------------------------------------------------------------------+

2.2 Create room
+--------------------------------------------------------------------------+
| CREATE ROOM                                                              |
+--------------------------------------------------------------------------+
| Branch *             [Main Branch v]                                    |
| Floor *              [3rd Floor v]                                      |
|                                                                          |
| Room Number *        [301____________]                                   |
| Room Name            [Doctor Chamber 301________]                        |
| Room Type            [Consultation Room v]                               |
|                                                                          |
| Room Capacity        [1 doctor v]                                        |
| Public Display      [Enabled v]                                         |
|                                                                          |
| Status               [Available v]                                      |
|                                                                          |
|                       [Cancel] [Create Room]                             |
+--------------------------------------------------------------------------+

Room capacity and room type should be configurable according to facility policy.
2.3 Room details
+--------------------------------------------------------------------------+
| ROOM 301                                             [Edit Room]         |
+--------------------------------------------------------------------------+
| Branch: Main Branch                                                     |
| Floor: 3rd Floor                                                        |
| Status: Active                                                          |
| Public Display: Enabled                                                 |
+--------------------------------------------------------------------------+
| CURRENT ASSIGNMENT                                                      |
| Doctor: Dr. Rahman                                                      |
| Session: 04:00 PM - 08:00 PM                                            |
|                                                                          |
| [View Doctor] [View Queue] [Change Assignment]                          |
+--------------------------------------------------------------------------+
| ASSIGNMENT HISTORY                                                      |
| Date       Doctor          Start       End          Status              |
| 06 Nov     Dr. Rahman      04:00 PM    08:00 PM     Active              |
| 05 Nov     Dr. Rahman      04:00 PM    08:00 PM     Completed           |
+--------------------------------------------------------------------------+

3. Doctor-room assignment
This is an important link between doctor scheduling and physical chamber operations.
3.1 Assignment directory
+--------------------------------------------------------------------------+
| DOCTOR-ROOM ASSIGNMENTS                              [+ New Assignment]  |
+--------------------------------------------------------------------------+
| Branch [Main v] Floor [All v] Date [Today v] Doctor [All v] [Search]     |
+--------------------------------------------------------------------------+
| DOCTOR       | ROOM | FLOOR     | SESSION       | STATUS    | ACTIONS   |
|--------------|------|-----------|---------------|-----------|-----------|
| Dr. Rahman   | 301  | 3rd       | 04-08 PM      | Active    | [View]    |
| Dr. Akter    | 302  | 3rd       | 04-09 PM      | Active    | [View]    |
| Dr. Hasan    | 303  | 3rd       | 05-09 PM      | Active    | [View]    |
+--------------------------------------------------------------------------+

3.2 New assignment
+--------------------------------------------------------------------------+
| ASSIGN DOCTOR TO ROOM                                                    |
+--------------------------------------------------------------------------+
| Doctor *              [Dr. Rahman v]                                    |
| Branch *              [Main Branch v]                                   |
| Floor *               [3rd Floor v]                                     |
| Room *                [301 - Available v]                               |
|                                                                          |
| Assignment Date *     [06 Nov 2026]                                     |
| Start Time *          [04:00 PM]                                        |
| End Time *            [08:00 PM]                                        |
|                                                                          |
| Existing Appointments [Show conflicting bookings]                       |
|                                                                          |
|                       [Cancel] [Confirm Assignment]                      |
+--------------------------------------------------------------------------+

3.3 Conflict warning
+--------------------------------------------------------------------------+
|                    ROOM / DOCTOR CONFLICT                                |
+--------------------------------------------------------------------------+
| Cannot complete assignment without resolving the conflict.              |
|                                                                          |
| Doctor: Dr. Rahman                                                       |
| Requested Room: 301                                                      |
| Requested Time: 04:00 PM - 08:00 PM                                     |
|                                                                          |
| CONFLICT                                                                 |
| Dr. Rahman is already assigned to Room 305 during this period.           |
|                                                                          |
| [Choose Another Room] [Choose Another Time] [Cancel]                    |
+--------------------------------------------------------------------------+

An assignment must never silently overwrite an existing assignment or appointment.
4. Room availability board
+--------------------------------------------------------------------------+
| ROOM AVAILABILITY                       MAIN BRANCH | 3RD FLOOR           |
+--------------------------------------------------------------------------+
| ROOM 301       ROOM 302       ROOM 303       ROOM 304                     |
| [OCCUPIED]     [OCCUPIED]     [OCCUPIED]     [AVAILABLE]                  |
| Dr. Rahman     Dr. Akter      Dr. Hasan      --                           |
|                                                                          |
+--------------------------------------------------------------------------+
| ROOM 305       ROOM 306       ROOM 307       ROOM 308                     |
| [ON BREAK]     [AVAILABLE]    [BLOCKED]      [OCCUPIED]                   |
| Dr. Sultana    --             Maintenance   Dr. Karim                    |
+--------------------------------------------------------------------------+
| [View Room] [Assign Doctor] [Block Room] [Release Room]                  |
+--------------------------------------------------------------------------+

Room status and doctor status should be separate. For example, a room may be available even if a doctor is on break elsewhere.
5. Walk-in registration
This is a critical reception workflow in Bangladesh, where patients frequently arrive directly at a hospital or chamber.
5.1 Walk-in registration
+--------------------------------------------------------------------------+
| NEW WALK-IN PATIENT                                                      |
+--------------------------------------------------------------------------+
| STEP 1 — PATIENT                                                        |
|                                                                          |
| Search Patient [Name / Mobile / Patient ID................] [Search]    |
|                                                                          |
| [ + Register New Patient ]                                               |
|                                                                          |
| Selected Patient: Rahim Uddin | 017XXXXXXX                               |
+--------------------------------------------------------------------------+
| STEP 2 — DOCTOR AND LOCATION                                             |
|                                                                          |
| Branch *              [Main Branch v]                                   |
| Floor *               [3rd Floor v]                                     |
| Doctor *              [Dr. Rahman v]                                    |
| Room                  [301 - Room 301]                                  |
+--------------------------------------------------------------------------+
| STEP 3 — QUEUE                                                          |
|                                                                          |
| Walk-in Policy:       [End of Queue v]                                  |
| Current Queue Size:   12                                                 |
| Assigned Position:    13                                                 |
| Token Number:         013                                                |
|                                                                          |
| Notes (optional)      [____________________________]                    |
|                                                                          |
|                       [Cancel] [Register Walk-in]                        |
+--------------------------------------------------------------------------+

The selected walk-in policy determines placement, subject to capacity and other configured rules.
5.2 Walk-in confirmation
+--------------------------------------------------------------------------+
| WALK-IN REGISTERED SUCCESSFULLY                                         |
+--------------------------------------------------------------------------+
|                                                                          |
| Patient:          Rahim Uddin                                            |
| Doctor:           Dr. Rahman                                             |
| Room:             301                                                    |
| Floor:            3rd Floor                                              |
| Token Number:     013                                                    |
| Queue Position:   13                                                     |
|                                                                          |
| [Print Token Slip]    [Register Another]    [View Queue]                 |
+--------------------------------------------------------------------------+

5.3 Token slip
+------------------------------------------+
|              CITY HOSPITAL               |
|                MAIN BRANCH               |
|------------------------------------------|
| PATIENT TOKEN                             |
|                                          |
| TOKEN NO:             013                |
|                                          |
| DOCTOR:           Dr. Rahman             |
| ROOM:                 301                |
| FLOOR:           3rd Floor               |
| DATE:           06 Nov 2026              |
|                                          |
| Please wait until your token is called. |
| আপনার টোকেন নম্বরের জন্য অপেক্ষা করুন।  |
|------------------------------------------|
| Appointment ID: APT-00013                |
+------------------------------------------+

The receipt is a convenience for the patient. The appointment and queue record remain authoritative.
6. Walk-in policy configuration
+--------------------------------------------------------------------------+
| WALK-IN QUEUE POLICY                                                     |
+--------------------------------------------------------------------------+
| Branch: Main Branch      Doctor: Dr. Rahman                              |
+--------------------------------------------------------------------------+
| WALK-IN PLACEMENT                                                        |
|                                                                          |
| ( ) End of Queue                                                          |
| ( ) First Come, First Served                                              |
| ( ) Reserved Walk-in Capacity                                             |
| ( ) Staff-Selected Queue Position                                         |
|                                                                          |
| RESERVED CAPACITY                                                        |
|                                                                          |
| Maximum Walk-in Capacity       [5]                                       |
| Maximum Total Queue Capacity   [30]                                      |
|                                                                          |
| STAFF PLACEMENT                                                          |
|                                                                          |
| Allow Manual Placement          [✓]                                       |
| Require Reason                  [✓]                                       |
|                                                                          |
|                        [Cancel] [Save Policy]                            |
+--------------------------------------------------------------------------+

The system must reject any placement that violates configured capacity.
7. Appointment rescheduling
7.1 Reschedule appointment
+--------------------------------------------------------------------------+
| RESCHEDULE APPOINTMENT                                                   |
+--------------------------------------------------------------------------+
| Original Appointment: APT-001                                           |
| Patient: Rahim Uddin                                                     |
| Doctor: Dr. Rahman                                                       |
|                                                                          |
| CURRENT APPOINTMENT                                                      |
| Date: 06 Nov 2026        Time: 04:00 PM                                  |
|                                                                          |
| NEW APPOINTMENT                                                          |
| Branch *            [Main Branch v]                                     |
| Doctor *            [Dr. Rahman v]                                     |
| Date *              [07 Nov 2026]                                       |
| Available Time      [04:30 PM v]                                        |
|                                                                          |
| Reason *            [Patient requested change________]                  |
|                                                                          |
|                        [Cancel] [Confirm Reschedule]                     |
+--------------------------------------------------------------------------+

7.2 Reschedule confirmation
+--------------------------------------------------------------------------+
| APPOINTMENT RESCHEDULED                                                  |
+--------------------------------------------------------------------------+
| Original: APT-001                                                        |
| Status: RESCHEDULED                                                      |
|                                                                          |
| New Appointment: APT-024                                                 |
| Status: BOOKED                                                           |
| Linked to: APT-001                                                       |
|                                                                          |
| [View Original] [View New Appointment]                                   |
+--------------------------------------------------------------------------+

The original appointment must remain in history. Do not overwrite it.
8. Cancellation management
+--------------------------------------------------------------------------+
| CANCEL APPOINTMENT                                                       |
+--------------------------------------------------------------------------+
| Appointment ID: APT-001                                                  |
| Patient: Rahim Uddin                                                     |
| Doctor: Dr. Rahman                                                       |
| Date: 06 Nov 2026                                                        |
|                                                                          |
| Cancellation Reason *                                                    |
| [Patient requested cancellation v]                                      |
|                                                                          |
| Additional Notes                                                         |
| [______________________________________________]                         |
|                                                                          |
| This action will release eligible appointment capacity.                 |
|                                                                          |
|                       [Go Back] [Confirm Cancellation]                   |
+--------------------------------------------------------------------------+

9. No-show and late-arrival management
9.1 Appointment attendance board
+--------------------------------------------------------------------------+
| ATTENDANCE MANAGEMENT                                                    |
+--------------------------------------------------------------------------+
| Doctor [All v] Branch [Main v] Date [Today v] Status [All v] [Search]   |
+--------------------------------------------------------------------------+
| PATIENT       | APPOINTMENT | TIME    | ARRIVAL | STATUS    | ACTIONS   |
|---------------|-------------|---------|---------|-----------|-----------|
| Rahim Uddin   | APT-001     | 04:00   | 03:50   | Present   | [View]    |
| Salma Akter   | APT-002     | 04:15   | 04:30   | Late      | [View]    |
| Karim Hasan   | APT-003     | 04:30   | --      | Pending   | [View]    |
+--------------------------------------------------------------------------+

9.2 Mark no-show
+--------------------------------------------------------------------------+
| CONFIRM NO-SHOW                                                          |
+--------------------------------------------------------------------------+
| Patient: Karim Hasan                                                     |
| Appointment: APT-003                                                     |
| Scheduled Time: 04:30 PM                                                 |
| Grace Period: 15 minutes                                                 |
|                                                                          |
| Has the patient failed to arrive?                                        |
|                                                                          |
| ( ) Yes — Confirm No-Show                                                |
| ( ) No — Patient is present                                              |
|                                                                          |
| Reason / Notes: [____________________________________]                   |
|                                                                          |
|                    [Cancel] [Confirm Attendance Status]                 |
+--------------------------------------------------------------------------+

The system must not automatically mark a patient as a no-show. Staff confirms the status.
10. Doctor availability board
+--------------------------------------------------------------------------+
| DOCTOR AVAILABILITY                              MAIN BRANCH              |
+--------------------------------------------------------------------------+
| DATE: 06 NOV 2026                                                         |
+--------------------------------------------------------------------------+
| DOCTOR        | ROOM | SESSION       | STATUS          | ACTIONS          |
|---------------|------|---------------|-----------------|------------------|
| Dr. Rahman    | 301  | 04-08 PM      | Serving         | [View]           |
| Dr. Akter     | 302  | 04-09 PM      | Serving         | [View]           |
| Dr. Hasan     | 303  | 05-09 PM      | Delayed         | [View]           |
| Dr. Islam     | 304  | 04-08 PM      | Available       | [View]           |
| Dr. Sultana   | 305  | 04-08 PM      | On Break        | [View]           |
| Dr. Karim     | 306  | 04-08 PM      | Unavailable     | [View]           |
+--------------------------------------------------------------------------+

11. Doctor session management
This allows staff to start, pause, resume and close an operational session.
11.1 Session control
+--------------------------------------------------------------------------+
| DOCTOR SESSION CONTROL                                                   |
+--------------------------------------------------------------------------+
| Doctor: Dr. Rahman                                                       |
| Branch: Main Branch                                                      |
| Room: 301                                                                |
| Scheduled: 04:00 PM - 08:00 PM                                           |
|                                                                          |
| SESSION STATUS: ACTIVE                                                   |
|                                                                          |
| Appointments: 18                                                         |
| Completed: 8                                                            |
| Waiting: 6                                                              |
| In Consultation: 1                                                      |
| Remaining: 3                                                            |
|                                                                          |
| [Pause Session] [Resume Session] [Close Session]                         |
+--------------------------------------------------------------------------+

11.2 Close session confirmation
+--------------------------------------------------------------------------+
| CLOSE DOCTOR SESSION?                                                    |
+--------------------------------------------------------------------------+
| There are 3 patients remaining in the queue.                             |
|                                                                          |
| Review the remaining appointments before closing.                       |
|                                                                          |
| [Review Queue]                                                           |
|                                                                          |
| Closing this session will not delete or complete pending appointments.  |
|                                                                          |
|                         [Cancel] [Close Session]                         |
+--------------------------------------------------------------------------+

12. Queue history
+--------------------------------------------------------------------------+
| QUEUE HISTORY                                                            |
+--------------------------------------------------------------------------+
| Doctor [Dr. Rahman v] Date [06 Nov 2026] Token [All v] [Search]           |
+--------------------------------------------------------------------------+
| TOKEN | PATIENT       | CREATED | FINAL STATUS | LAST POSITION | ACTION |
|-------|---------------|---------|--------------|---------------|--------|
| 001   | Rahim Uddin   | 04:00   | Completed    | 01            | [View] |
| 002   | Salma Akter   | 04:10   | Completed    | 02            | [View] |
| 003   | Karim Hasan   | 04:20   | Skipped      | 03            | [View] |
| 004   | Nadia Islam   | 04:30   | In Queue     | 04            | [View] |
+--------------------------------------------------------------------------+

Queue movement audit
+--------------------------------------------------------------------------+
| QUEUE MOVEMENT DETAILS                                                   |
+--------------------------------------------------------------------------+
| Token: 003                                                               |
| Appointment: APT-003                                                     |
|                                                                          |
| TIME       OLD POSITION   NEW POSITION   ACTOR       REASON              |
|--------------------------------------------------------------------------|
| 04:20 PM   --             03             Staff A     Initial assignment  |
| 04:35 PM   03             04             Staff B     Patient unavailable|
| 04:45 PM   04             03             Staff B     Repositioned        |
+--------------------------------------------------------------------------+

13. Floor display management
This is the authenticated configuration screen for the public display.
13.1 Display directory
+--------------------------------------------------------------------------+
| PUBLIC DISPLAY MANAGEMENT                              [+ Add Display]   |
+--------------------------------------------------------------------------+
| Branch [Main v] Floor [All v] Status [All v] [Search]                    |
+--------------------------------------------------------------------------+
| DISPLAY ID | DISPLAY NAME       | FLOOR | TYPE       | STATUS | ACTIONS |
|------------|--------------------|-------|------------|--------|---------|
| DSP-001    | 3rd Floor TV       | 3rd   | Floor-wide | Online | [View]  |
| DSP-002    | Room 301 Display   | 3rd   | Chamber    | Online | [View]  |
| DSP-003    | 2nd Floor TV       | 2nd   | Floor-wide | Offline| [View]  |
+--------------------------------------------------------------------------+

13.2 Configure display
+--------------------------------------------------------------------------+
| CONFIGURE PUBLIC DISPLAY                                                 |
+--------------------------------------------------------------------------+
| Display Name *       [3rd Floor TV_________________]                     |
| Branch *             [Main Branch v]                                     |
| Floor *              [3rd Floor v]                                       |
| Display Type         [Floor-wide v]                                      |
|                                                                          |
| DISPLAY OPTIONS                                                          |
| Show Doctor Name     [✓]                                                 |
| Show Specialty       [✓]                                                 |
| Show Room Number     [✓]                                                 |
| Show Current Token   [✓]                                                 |
| Show Next Tokens     [✓]                                                 |
| Show Patient Name    [ ]                                                 |
|                                                                          |
| Language             [Bangla + English v]                                |
| Refresh Mode         [Live Updates v]                                    |
|                                                                          |
|                      [Preview] [Save Display]                            |
+--------------------------------------------------------------------------+

Patient names remain disabled for public displays.
13.3 Display health
+--------------------------------------------------------------------------+
| DISPLAY CONNECTION STATUS                                                |
+--------------------------------------------------------------------------+
| Display: 3rd Floor TV                                                    |
| Status: ONLINE                                                           |
| Last Updated: 05:42:18 PM                                                |
| Last Heartbeat: 05:42:18 PM                                              |
|                                                                          |
| [Preview Display] [Disable Display]                                      |
+--------------------------------------------------------------------------+

If disconnected, the public display should show a clear stale-data warning and last update time.
14. Branch switching
+--------------------------------------------------------------------------+
| SELECT WORKING BRANCH                                                    |
+--------------------------------------------------------------------------+
| Your assigned branches:                                                  |
|                                                                          |
| +--------------------------------------------------------------------+   |
| | Main Branch                                      [ACTIVE]          |   |
| | Dhaka                                                               |   |
| | [Continue]                                                          |   |
| +--------------------------------------------------------------------+   |
|                                                                          |
| +--------------------------------------------------------------------+   |
| | Uttara Branch                                                       |   |
| | Uttara, Dhaka                                                       |   |
| | [Switch to Branch]                                                  |   |
| +--------------------------------------------------------------------+   |
|                                                                          |
| +--------------------------------------------------------------------+   |
| | Mirpur Branch                                                       |   |
| | Mirpur, Dhaka                                                       |   |
| | [Switch to Branch]                                                  |   |
| +--------------------------------------------------------------------+   |
+--------------------------------------------------------------------------+

Changing branch must update the authorized data scope throughout the application.
15. Permission management
The approved six roles remain fixed. Permissions determine which actions each role can perform.
15.1 Permission matrix
+--------------------------------------------------------------------------+
| ROLE PERMISSIONS                                                         |
+--------------------------------------------------------------------------+
| MODULE / ACTION | ORG ADMIN | BRANCH ADMIN | RECEPTION | DOCTOR | ASST   |
|-----------------|-----------|--------------|-----------|--------|--------|
| View Patients   |    Yes    |     Yes      |    Yes    |  Yes*  | Yes*   |
| Create Patients |    Yes    |     Yes      |    Yes    |   No   | No     |
| Edit Patients   |    Yes    |     Yes      |    Yes    |  Yes*  | Yes*   |
| Book Appointment|    Yes    |     Yes      |    Yes    |   No   | No     |
| Check-in        |    Yes    |     Yes      |    Yes    |   No   | Yes    |
| Queue Control   |    Yes    |     Yes      |    Yes    |  Own   | Assign. |
| Manage Doctors  |    Yes    |     Yes      |     No    |   No   | No     |
| Manage Rooms    |    Yes    |     Yes      |     No    |   No   | No     |
| View Audit Logs |    Yes    |     Yes      |     No    |   No   | No     |
+--------------------------------------------------------------------------+
| * Subject to explicitly granted permissions and organization policy.     |
+--------------------------------------------------------------------------+

This is a proposed permission baseline, not a replacement for the final authorization specification.
15.2 Permission detail
+--------------------------------------------------------------------------+
| CONFIGURE ROLE: RECEPTIONIST                                             |
+--------------------------------------------------------------------------+
| PATIENTS                                                                 |
| [✓] View patient records                                                 |
| [✓] Register new patients                                                |
| [✓] Edit patient information                                             |
| [ ] Merge patient records                                                |
|                                                                          |
| APPOINTMENTS                                                             |
| [✓] Create appointment                                                   |
| [✓] Reschedule appointment                                               |
| [✓] Cancel appointment                                                   |
|                                                                          |
| QUEUE                                                                    |
| [✓] Check in patients                                                    |
| [✓] Reorder queue                                                        |
| [✓] Mark skipped                                                        |
| [ ] Close doctor session                                                 |
|                                                                          |
| ROOMS                                                                    |
| [ ] Create room                                                         |
| [ ] Change doctor-room assignment                                        |
|                                                                          |
|                          [Cancel] [Save Permissions]                    |
+--------------------------------------------------------------------------+

16. Patient duplicate resolution
+--------------------------------------------------------------------------+
| POSSIBLE DUPLICATE PATIENTS                                              |
+--------------------------------------------------------------------------+
| Search: 017XXXXXXX                                                       |
+--------------------------------------------------------------------------+
| PATIENT ID | NAME         | MOBILE       | CREATED       | ACTIONS       |
|------------|--------------|--------------|---------------|---------------|
| PAT-001    | Rahim Uddin  | 017XXXXXXX   | 01 Nov 2026   | [View]        |
| PAT-024    | Rahim Uddin  | 017XXXXXXX   | 06 Nov 2026   | [View]        |
+--------------------------------------------------------------------------+
|                                                                          |
| These records may belong to the same person.                             |
| Do not merge automatically.                                              |
|                                                                          |
| [Keep Separate] [Request Authorized Merge]                               |
+--------------------------------------------------------------------------+

Authorized merge review
+--------------------------------------------------------------------------+
| REVIEW PATIENT MERGE                                                     |
+--------------------------------------------------------------------------+
| PRIMARY RECORD: PAT-001                                                  |
| SECONDARY RECORD: PAT-024                                                |
|                                                                          |
| Compare patient information and appointment histories.                  |
|                                                                          |
| [ ] I have verified that both records belong to the same patient.       |
|                                                                          |
| Reason for merge * [________________________________]                    |
|                                                                          |
|                       [Cancel] [Confirm Merge]                           |
+--------------------------------------------------------------------------+

This is a controlled operation, not an automatic deduplication process.
17. Capacity management
+--------------------------------------------------------------------------+
| APPOINTMENT CAPACITY CONFIGURATION                                       |
+--------------------------------------------------------------------------+
| Branch: Main Branch       Doctor: Dr. Rahman                             |
| Schedule: Saturday 04:00 PM - 08:00 PM                                   |
+--------------------------------------------------------------------------+
| CAPACITY LEVELS                                                          |
|                                                                          |
| Maximum time-slot capacity          [1 patient per slot]                 |
| Maximum serial capacity             [30 patients]                       |
| Maximum hybrid capacity             [25 scheduled + 5 walk-in]           |
|                                                                          |
| Overbooking                        [ ] Disabled                          |
|                                                                          |
| WALK-IN RESERVATION                                                      |
| Reserved walk-in capacity           [5]                                  |
|                                                                          |
| [Preview Capacity] [Save Configuration]                                  |
+--------------------------------------------------------------------------+

Capacity must be checked atomically during booking to prevent double-booking.
18. Schedule conflict management
+--------------------------------------------------------------------------+
| SCHEDULE CONFLICTS                                                       |
+--------------------------------------------------------------------------+
| Branch [Main v] Date [06 Nov 2026] Status [Unresolved v]                 |
+--------------------------------------------------------------------------+
| CONFLICT ID | DOCTOR       | CONFLICT TYPE      | STATUS   | ACTIONS     |
|-------------|--------------|-------------------|----------|-------------|
| CF-001      | Dr. Rahman   | Overlapping time   | Open     | [Resolve]  |
| CF-002      | Dr. Akter    | Room unavailable   | Open     | [Resolve]  |
+--------------------------------------------------------------------------+

Resolve conflict
+--------------------------------------------------------------------------+
| RESOLVE SCHEDULE CONFLICT                                                |
+--------------------------------------------------------------------------+
| Doctor: Dr. Rahman                                                       |
| Existing: Room 301 | 04:00 PM - 08:00 PM                                 |
| Requested: Room 305 | 04:00 PM - 08:00 PM                                |
|                                                                          |
| Possible actions:                                                        |
|                                                                          |
| ( ) Choose another room                                                 |
| ( ) Choose another time                                                 |
| ( ) Cancel proposed assignment                                           |
|                                                                          |
| Reason * [_________________________________________]                     |
|                                                                          |
|                        [Cancel] [Save Resolution]                        |
+--------------------------------------------------------------------------+

19. Appointment search
+--------------------------------------------------------------------------+
| GLOBAL APPOINTMENT SEARCH                                                |
+--------------------------------------------------------------------------+
| Search by:                                                               |
|                                                                          |
| [Appointment ID / Patient ID / Patient Name / Mobile................]   |
|                                                                          |
| Filters: [Date v] [Branch v] [Doctor v] [Status v]                       |
|                                                                          |
| [Search]                                                                 |
+--------------------------------------------------------------------------+
| RESULTS                                                                  |
|                                                                          |
| APT-001 | Rahim Uddin | Dr. Rahman | Room 301 | Confirmed                |
| APT-024 | Rahim Uddin | Dr. Rahman | Room 301 | Booked                   |
|                                                                          |
| [View Appointment]                                                       |
+--------------------------------------------------------------------------+

Search results must remain within the user's organization and branch permissions.
20. Subscription expiry and read-only state
+--------------------------------------------------------------------------+
|                       SUBSCRIPTION EXPIRED                               |
+--------------------------------------------------------------------------+
|                                                                          |
| Your organization's subscription has expired.                           |
|                                                                          |
| Current Status: READ-ONLY                                                |
|                                                                          |
| You can still:                                                           |
|   - View existing patients                                               |
|   - View appointment history                                             |
|   - View doctor records                                                  |
|   - Export permitted records                                             |
|                                                                          |
| You cannot:                                                              |
|   - Create new appointments                                              |
|   - Modify patient records                                               |
|   - Change doctor schedules                                               |
|   - Modify queue operations                                               |
|                                                                          |
| Existing data has been retained.                                         |
|                                                                          |
| [Contact Administrator]                                                  |
+--------------------------------------------------------------------------+

The application must clearly disable unavailable actions instead of allowing users to submit operations that will fail.
21. Final additional screen inventory
These complete the remaining screen designs.
#	Screen	Priority
1	Floor directory and creation	P0
2	Floor details	P0
3	Room directory and creation	P0
4	Room details	P0
5	Doctor-room assignment	P0
6	Room availability	P1
7	Walk-in registration	P0
8	Walk-in confirmation and token slip	P0
9	Walk-in policy configuration	P0
10	Appointment rescheduling	P0
11	Appointment cancellation	P0
12	No-show management	P0
13	Doctor availability	P1
14	Doctor session management	P0
15	Queue history	P0
16	Floor display management	P0
17	Display connection status	P1
18	Branch switching	P0
19	Permission management	P0
20	Duplicate patient resolution	P1
21	Capacity management	P0
22	Schedule conflict resolution	P0
23	Appointment search	P0
24	Subscription read-only state	P0


22. Updated AMSDP navigation architecture
With the new screens, I recommend this final navigation structure:
AMSDP
|
+-- DASHBOARD
|    +-- Today's Overview
|    +-- Operational Alerts
|
+-- APPOINTMENT OPERATIONS
|    +-- Appointment List
|    +-- New Appointment
|    +-- Walk-in Registration
|    +-- Appointment Search
|    +-- Cancellation / Rescheduling
|
+-- QUEUE MANAGEMENT
|    +-- Live Queue
|    +-- Queue History
|    +-- Attendance / No-show
|    +-- Doctor Session Control
|
+-- PATIENTS
|    +-- Patient Directory
|    +-- Register Patient
|    +-- Duplicate Review
|
+-- DOCTORS
|    +-- Doctor Directory
|    +-- Doctor Details
|    +-- Doctor Availability
|    +-- Doctor Schedules
|
+-- FACILITY MANAGEMENT
|    +-- Branches
|    +-- Floors
|    +-- Rooms / Chambers
|    +-- Doctor-room Assignments
|    +-- Room Availability
|
+-- PUBLIC DISPLAYS
|    +-- Floor Displays
|    +-- Chamber Displays
|    +-- Display Configuration
|    +-- Display Health
|
+-- ORGANIZATION ADMINISTRATION
|    +-- Staff
|    +-- Roles and Permissions
|    +-- Organization Settings
|    +-- Capacity and Walk-in Policies
|    +-- Subscription
|    +-- Audit Logs
|
+-- SYSTEM ADMINISTRATION
     +-- Organizations
     +-- Subscription Plans
     +-- Global Configuration

23. Three UI rules I would make mandatory for AILI's Frontend Developer
1. No dead controls: Every button, dropdown, tab and action must have a working behavior or be visibly disabled with an explanation.
2. Operational consistency: A room assignment, appointment status or queue change must immediately reflect wherever that information is displayed, subject to reliable update confirmation.
3. Bangladesh-first usability: Responsive layouts, Bangla Unicode, large touch targets, clear room/token numbers, low-bandwidth behavior and printable lightweight receipts.

AMSDP needs two separate applications or clearly separated workspaces:
1. AMSDP Platform Admin — operated by you or your authorized platform team.
2. Organization Users — operated by hospitals, clinics, diagnostic centres and their staff.
1. AMSDP Platform Admin
(Needs complete UI/UX design)

This is the control centre for the entire SaaS platform.
Module	Screens to design
Platform Dashboard	Platform overview, KPIs, operational alerts
Organization Management	Organization list, registration, details, suspension
Branch Oversight	All branches, status, organization association
Subscription Plans	Plan creation, pricing configuration, limits
Subscription Management	Active, expired, grace period, read-only
Platform Users	Super Admin accounts and permissions
Global Configuration	System-wide defaults, feature options and limits
System Monitoring	Service health, errors, availability
Audit & Security	Platform audit logs, access history
Support Operations	Organization support requests and account assistance
Platform Reports	Organization growth, usage, subscription statistics


Platform Admin dashboard — proposed wireframe
+----------------------------------------------------------------------------+
| AMSDP PLATFORM ADMIN                    [Notifications] [Admin] [Logout]   |
+----------------------+-----------------------------------------------------+
| PLATFORM             | PLATFORM OVERVIEW                                   |
|                      |                                                     |
| > Dashboard          | Organizations     Active Subscriptions              |
|   Organizations      |      125                 98                          |
|   Branches           |                                                     |
|   Subscriptions      | Doctors           Appointments Today                |
|   Plans              |      850                2,450                         |
|                      |                                                     |
| PLATFORM CONTROL     +-----------------------------------------------------+
|   Platform Users     | ORGANIZATION ACTIVITY                                |
|   Global Settings    |                                                     |
|   Feature Limits     | Organization       Branches   Status   Subscription |
|                      | City Hospital         3       Active     Pro        |
| MONITORING           | Green Clinic          2       Active     Basic      |
|   System Health      | Care Diagnostic       1       Expired    Basic      |
|   Audit Logs         |                                                     |
|   Security           +-----------------------------------------------------+
|                      | PLATFORM ALERTS                                     |
| REPORTS              | ! Subscription expired: Care Diagnostic             |
|   Usage Reports      | ! Organization approaching branch limit             |
|   Growth Reports     | ! Service health warning                             |
+----------------------+-----------------------------------------------------+

2. Organization Admin workspace
(Partially designed)

This is the workspace for each hospital or clinic administrator.

We have already designed organizations, branches, staff, doctors, patients, rooms, schedules, appointments, queues, settings, subscriptions and audit logs.

However, the complete organization onboarding and configuration experience still needs to be designed.
+----------------------------------------------------------------------------+
| CITY HOSPITAL                         [Branch: Main v] [Admin] [Logout]    |
+----------------------+-----------------------------------------------------+
| ORGANIZATION         | ORGANIZATION DASHBOARD                              |
|                      |                                                     |
| > Dashboard          | Branches       Doctors       Staff       Rooms      |
|   Branches           |    3              25            40          18       |
|   Staff              |                                                     |
|   Roles              +-----------------------------------------------------+
|                      | APPOINTMENT OPERATIONS                              |
| FACILITY             |                                                     |
|   Doctors            | Today's Appointments      Waiting Patients          |
|   Patients           |       86                       23                    |
|   Floors             |                                                     |
|   Rooms              +-----------------------------------------------------+
|   Schedules          | BRANCH PERFORMANCE                                  |
|                      | Main Branch      48 appointments                    |
| OPERATIONS           | Uttara Branch    22 appointments                    |
|   Appointments       | Mirpur Branch    16 appointments                    |
|   Queue              |                                                     |
|   Public Displays    +-----------------------------------------------------+
|                      | ADMINISTRATION                                     |
| SETTINGS             | Organization Settings | Capacity | Subscription     |
|   General            |                                                     |
|   Capacity           |                                                     |
|   Subscription       |                                                     |
|   Audit Logs         |                                                     |
+----------------------+-----------------------------------------------------+

3. Branch Admin workspace
The Branch Admin should have a more focused interface.
+----------------------------------------------------------------------------+
| CITY HOSPITAL                       MAIN BRANCH [Branch Admin]              |
+----------------------+-----------------------------------------------------+
| > Dashboard          | BRANCH OPERATIONS                                   |
|   Doctors            |                                                     |
|   Patients           | Doctors Working: 12    Rooms Active: 10              |
|   Rooms              | Appointments: 48       Waiting: 15                  |
|   Floors             |                                                     |
|   Schedules          +-----------------------------------------------------+
|   Appointments       | DOCTOR / ROOM STATUS                                |
|   Queue              |                                                     |
|   Staff              | Dr. Rahman     Room 301     Serving                  |
|   Displays           | Dr. Akter      Room 302     Serving                  |
|   Audit Logs         | Dr. Hasan      Room 303     Delayed                  |
|                      |                                                     |
+----------------------+-----------------------------------------------------+

4. What is still missing from the complete platform UI/UX?
Area	Current state
Platform Admin	Initial dashboard only
Platform organization management	Partially covered
Subscription plans and limits	Needs full design
Platform-level user management	Needs design
Global configuration	Needs design
Organization onboarding wizard	Needs design
Organization Admin	Partially covered
Branch Admin	Partially covered
Receptionist	Operational screens covered
Doctor workspace	Needs dedicated design
Doctor Assistant workspace	Needs dedicated design
Public floor display	Designed
Individual chamber display	Designed


5. My recommended final architecture
I would organize AMSDP into these distinct experiences:

AMSDP Platform

SaaS control plane

Platform Admin → Organizations → Plans → Subscriptions → Global Configuration

Organization Workspace

Tenant administration

Organization Admin → Branches → Staff → Facility Configuration

Branch Operations

Daily hospital operations

Branch Admin → Receptionist → Doctor → Doctor Assistant

Public Interfaces

Read-only displays

Floor-wide Doctor/Token Display → Individual Chamber Display

My recommendation: Before we hand the UI specification to AILI's Frontend Developer, let's complete the Platform Admin, Organization Onboarding, Doctor Workspace and Assistant Workspace. Those are the remaining major gaps.

That will give us a much more complete product specification rather than developing the facility screens first and discovering missing platform administration later.













finish UI for Platform Admin, Organization Onboarding, Doctor Workspace and Assistant Workspace.












AMSDP — Remaining UI/UX Blueprint
This completes the four outstanding areas:
1. Platform Admin — controls the AMSDP SaaS platform.
2. Organization Onboarding — registers and configures a new hospital, clinic, or diagnostic centre.
3. Doctor Workspace — gives doctors a focused view of their own appointments, patients, and queue.
4. Assistant Workspace — helps assistants manage their assigned doctor's chamber and queue.
The designs follow the approved AMSDP scope: facility-centric multi-tenancy, six roles, staff-mediated patient registration, configurable appointments and queues, and no patient portal, EMR, billing ledger, or clinical records.
1. Platform Admin UI
Platform Admin is the AMSDP SaaS control plane. It is separate from an organization's workspace.

Only super_admin should access these screens.
1.1 Platform Admin — Main Layout
+--------------------------------------------------------------------------------+
| AMSDP PLATFORM                                  Super Admin     [Profile] [Exit]|
+--------------------------------------------------------------------------------+
| SIDEBAR                          | MAIN CONTENT                                |
|                                  |                                              |
| > Dashboard                      |                                              |
|   Organizations                  |                                              |
|   Onboarding Requests            |                                              |
|   Branch Oversight               |                                              |
|   Subscription Plans             |                                              |
|   Subscriptions                  |                                              |
|   Platform Users                 |                                              |
|   Global Configuration           |                                              |
|   System Monitoring              |                                              |
|   Audit & Security               |                                              |
|   Support Operations             |                                              |
|   Platform Reports               |                                              |
|                                  |                                              |
+--------------------------------------------------------------------------------+

Platform Admin should not normally handle an organization's day-to-day appointments or patients.
1.2 Platform Dashboard
+--------------------------------------------------------------------------------+
| Platform Dashboard                                           [Date Range v]    |
+--------------------------------------------------------------------------------+
| ORGANIZATIONS       ACTIVE BRANCHES       TOTAL STAFF       ACTIVE SUBSCRIPTIONS|
|       128                 246                1,840                 112           |
|                                                                                |
| PENDING ONBOARDING    TRIAL ACCOUNTS       EXPIRING SOON       SUSPENDED         |
|        7                   12                   5                  4             |
+--------------------------------------------------------------------------------+
| ORGANIZATION GROWTH                    SUBSCRIPTION OVERVIEW                    |
| +--------------------------------+     +-------------------------------------+  |
| |                                |     | Active       112                    |  |
| |     [Growth Chart]             |     | Trial         12                    |  |
| |                                |     | Expired        8                    |  |
| |                                |     | Suspended      4                    |  |
| +--------------------------------+     +-------------------------------------+  |
|                                                                                |
| RECENT ORGANIZATIONS                                                           |
| +----------------------------------------------------------------------------+ |
| | Organization       | Type       | Branches | Status   | Created | Action   | |
| |--------------------|------------|----------|----------|---------|----------| |
| | City Hospital      | Hospital   | 3        | Active   | 05 Nov  | [View]   | |
| | Green Clinic       | Clinic     | 1        | Trial    | 04 Nov  | [View]   | |
| | Metro Diagnostics | Diagnostic | 2        | Pending  | 03 Nov  | [Review] | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| PLATFORM ALERTS                                                                |
| [!] 3 subscriptions expire within 7 days                                      |
| [!] 2 onboarding requests require review                                      |
| [!] 1 organization has repeated login failures                                |
+--------------------------------------------------------------------------------+

Dashboard KPIs are platform-wide aggregates. They should not expose patient-level information.
1.3 Organization Directory
+--------------------------------------------------------------------------------+
| Organizations                                             [+ Add Organization] |
+--------------------------------------------------------------------------------+
| Search [Organization name / ID________________]                                |
| Type [All v] Status [All v] Subscription [All v]       [Search] [Reset]        |
+--------------------------------------------------------------------------------+
| Organization ID | Name              | Type        | Branches | Status | Action |
|-----------------|-------------------|-------------|----------|--------|--------|
| ORG-0001        | City Hospital     | Hospital    | 3        | Active | [View] |
| ORG-0002        | Green Clinic      | Clinic      | 1        | Trial  | [View] |
| ORG-0003        | Metro Diagnostics | Diagnostic  | 2        | Active | [View] |
| ORG-0004        | Sunrise Medical   | Hospital    | 1        | Pending| [View] |
+--------------------------------------------------------------------------------+
| Showing 1–20 of 128                                      [<] 1 2 3 ... [>]    |
+--------------------------------------------------------------------------------+

1.4 Organization Details
+--------------------------------------------------------------------------------+
| Organization: City Hospital                                  [Edit] [More v]   |
+--------------------------------------------------------------------------------+
| Overview | Branches | Subscription | Admin Users | Activity | Audit           |
+--------------------------------------------------------------------------------+
| Organization Information                                                      |
| ID: ORG-0001                       Status: ACTIVE                              |
| Name: City Hospital                Type: Hospital                              |
| Contact: +8801XXXXXXXXX            Email: admin@cityhospital.example           |
| Created: 05 Nov 2026                Subscription: Standard                      |
|                                                                                |
| USAGE                                                                         |
| Branches: 3 / 5                  Staff: 42 / 100                                |
| Doctors: 18                      Patients: 12,450                               |
|                                                                                |
| BRANCHES                                                                       |
| +----------------------------------------------------------------------------+ |
| | Branch Name       | Location       | Staff | Status | Action               | |
| |-------------------|----------------|-------|--------|----------------------| |
| | Main Branch       | Dhaka          | 25    | Active | [View]               | |
| | North Branch      | Dhaka          | 10    | Active | [View]               | |
| | South Branch      | Narayanganj    | 7     | Active | [View]               | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| ADMINISTRATORS                                                                 |
| Name                 Mobile              Status              [View]             |
| Organization Admin   +8801XXXXXXXXX      Active                                 |
|                                                                                |
| PLATFORM ACTIONS                                                               |
| [Change Subscription] [Suspend Organization] [Reactivate] [View Audit]         |
+--------------------------------------------------------------------------------+

Platform suspension must not delete data. The system should retain organization data according to the platform's retention policy.
1.5 Onboarding Requests
+--------------------------------------------------------------------------------+
| Onboarding Requests                                                            |
+--------------------------------------------------------------------------------+
| Search [Name / Contact____________________] Status [Pending v] [Search]         |
+--------------------------------------------------------------------------------+
| Request ID | Organization      | Type       | Submitted | Status  | Action    |
|------------|-------------------|------------|-----------|---------|-----------|
| ONB-001    | Sunrise Medical   | Hospital   | 05 Nov    | Pending | [Review]  |
| ONB-002    | Care Point        | Clinic     | 04 Nov    | Pending | [Review]  |
| ONB-003    | Metro Diagnostics | Diagnostic | 03 Nov    | Approved| [View]    |
+--------------------------------------------------------------------------------+

Review onboarding request
+--------------------------------------------------------------------------------+
| Onboarding Review: ONB-001                                                     |
+--------------------------------------------------------------------------------+
| ORGANIZATION DETAILS                                                           |
| Organization Name: Sunrise Medical                                            |
| Organization Type: Hospital                                                   |
| Contact Person: [Name]                                                         |
| Mobile: [Number]                                                              |
| Email: [Email]                                                                |
| Address: [Address]                                                            |
|                                                                                |
| REQUESTED SETUP                                                               |
| Expected Branches: 2                                                          |
| Expected Doctors: 15                                                          |
| Expected Staff: 35                                                            |
|                                                                                |
| REVIEW NOTES                                                                   |
| [________________________________________________________________________]    |
|                                                                                |
| [Reject Request]                                     [Approve & Create]        |
+--------------------------------------------------------------------------------+

Approval creates or activates the organization and begins its onboarding process. It should not silently create unverified staff accounts.
1.6 Subscription Plans
+--------------------------------------------------------------------------------+
| Subscription Plans                                         [+ Create Plan]     |
+--------------------------------------------------------------------------------+
| Plan Name | Branch Limit | Staff Limit | Features | Status | Action            |
|-----------|--------------|-------------|----------|--------|-------------------|
| Starter   | 1            | 10          | Basic    | Active | [Edit]            |
| Standard  | 5            | 100         | Standard | Active | [Edit]            |
| Enterprise| Custom       | Custom      | Custom   | Active | [Edit]            |
+--------------------------------------------------------------------------------+

Plan configuration:
+--------------------------------------------------------------------------------+
| Create / Edit Subscription Plan                                                |
+--------------------------------------------------------------------------------+
| Plan Name: [________________________]                                          |
| Description: [___________________________________________________________]    |
|                                                                                |
| LIMITS                                                                         |
| Maximum Branches: [____]                                                       |
| Maximum Staff:    [____]                                                       |
|                                                                                |
| FEATURES                                                                       |
| [x] Appointment Management                                                     |
| [x] Queue Management                                                           |
| [x] Doctor Management                                                          |
| [x] Patient Management                                                         |
| [x] Public Queue Display                                                       |
|                                                                                |
| STATUS: [Active v]                                                             |
|                                                                                |
| [Cancel]                                                       [Save Plan]     |
+--------------------------------------------------------------------------------+

Only features and limits that AMSDP actually supports should be configurable.
1.7 Subscription Management
+--------------------------------------------------------------------------------+
| Subscriptions                                                                  |
+--------------------------------------------------------------------------------+
| Search [Organization________________] Status [All v] Plan [All v]              |
+--------------------------------------------------------------------------------+
| Organization      | Plan       | Start Date | End Date | Status  | Action      |
|-------------------|------------|------------|----------|---------|-------------|
| City Hospital     | Standard   | 01 Nov     | 01 Dec   | Active  | [Manage]    |
| Green Clinic      | Starter    | 01 Nov     | 08 Nov   | Trial   | [Manage]    |
| Metro Diagnostics| Standard   | 01 Oct     | 31 Oct   | Expired | [Manage]    |
+--------------------------------------------------------------------------------+

Subscription details
+--------------------------------------------------------------------------------+
| Subscription: City Hospital                                                    |
+--------------------------------------------------------------------------------+
| Current Plan: Standard                                                         |
| Status: ACTIVE                                                                 |
| Start Date: 01 Nov 2026                                                        |
| Expiry Date: 01 Dec 2026                                                       |
|                                                                                |
| USAGE                                                                         |
| Branches: 3 / 5                                                               |
| Staff: 42 / 100                                                               |
|                                                                                |
| [Change Plan] [Extend Subscription] [Suspend] [View History]                  |
+--------------------------------------------------------------------------------+

Subscription expiry rules:
- Active: normal operation.
- Grace period: normal operation, with warnings.
- Expired after grace period: read-only access.
- Data is retained; expiry must not delete records.
1.8 Platform Users
+--------------------------------------------------------------------------------+
| Platform Users                                               [+ Add User]      |
+--------------------------------------------------------------------------------+
| Search [Name / Mobile________________] Status [All v]                           |
+--------------------------------------------------------------------------------+
| Name              | Mobile          | Role        | Status | Action             |
|-------------------|-----------------|-------------|--------|--------------------|
| Platform Admin 1  | +8801XXXXXXXXX  | super_admin | Active | [Edit]             |
| Platform Admin 2  | +8801XXXXXXXXX  | super_admin | Active | [Edit]             |
+--------------------------------------------------------------------------------+

Platform users are not the same as organization staff. Organization admins cannot grant themselves super_admin.
1.9 Global Configuration
+--------------------------------------------------------------------------------+
| Global Configuration                                                          |
+--------------------------------------------------------------------------------+
| General | Security | Defaults | Limits | Localization                          |
+--------------------------------------------------------------------------------+
| DEFAULT SYSTEM SETTINGS                                                       |
| Default Language: [English v]                                                 |
| Supported Languages: [x] English  [x] বাংলা                                  |
|                                                                                |
| SECURITY                                                                       |
| Session Expiry: [____] minutes                                                 |
| Login Failure Limit: [____]                                                   |
|                                                                                |
| PLATFORM DEFAULTS                                                              |
| Default Grace Period: [____] days                                              |
| Default Organization Status: [Pending v]                                      |
|                                                                                |
| [Discard Changes]                                               [Save]         |
+--------------------------------------------------------------------------------+

Changes to global defaults should affect new organizations or explicitly selected organizations, not silently overwrite existing organization settings.
1.10 System Monitoring and Audit
+--------------------------------------------------------------------------------+
| System Monitoring                                                             |
+--------------------------------------------------------------------------------+
| Service             | Status       | Last Check | Action                       |
|---------------------|--------------|------------|------------------------------|
| Authentication      | Operational  | 11:28      | [Details]                    |
| Organization API    | Operational  | 11:28      | [Details]                    |
| Appointment API     | Operational  | 11:28      | [Details]                    |
| Queue API           | Operational  | 11:28      | [Details]                    |
| Database            | Operational  | 11:28      | [Details]                    |
+--------------------------------------------------------------------------------+
| Recent Incidents                                                             |
| [No active incidents]                                                        |
+--------------------------------------------------------------------------------+

+--------------------------------------------------------------------------------+
| Platform Audit Log                                                            |
+--------------------------------------------------------------------------------+
| Date Range [__________] Actor [All v] Action [All v] [Search]                  |
+--------------------------------------------------------------------------------+
| Time       | Actor          | Action              | Target       | Result      |
|------------|----------------|---------------------|--------------|-------------|
| 11:20      | Super Admin 1  | Plan Updated        | Standard     | Success     |
| 10:55      | Super Admin 2  | Org Suspended       | ORG-0008     | Success     |
+--------------------------------------------------------------------------------+

2. Organization Onboarding UI
Onboarding is the controlled process of setting up a new tenant.

The intended flow is:
1. Organization registration — name, type, contact and address.
2. Platform review — approval and subscription assignment.
3. Organization profile — timezone, language and organization defaults.
4. First branch — create the initial operating location.
5. Facility setup — floors and rooms.
6. Organization administrator — create the first admin account.
7. Staff and doctors — add users and doctor profiles.
8. Schedules and queues — configure appointment and walk-in policies.
9. Review and activation — verify the setup and start operations.
2.1 Onboarding Wizard — Main Layout
+--------------------------------------------------------------------------------+
| AMSDP                                                     Organization Setup   |
+--------------------------------------------------------------------------------+
| SETUP PROGRESS                                                                 |
|                                                                                |
| [1 Organization] -- [2 Branch] -- [3 Facility] -- [4 Admin]                    |
|        |                                                    |                  |
|        +------ [5 Doctors & Staff] -- [6 Operations] -- [7 Review]             |
+--------------------------------------------------------------------------------+
|                                                                                |
|                         ORGANIZATION REGISTRATION                             |
|                                                                                |
| Organization Name:       [________________________________________]           |
| Organization Type:        [Hospital v]                                        |
| Contact Person:           [________________________________________]           |
| Mobile Number:            [+880 _________________________________]            |
| Email Address:            [________________________________________]           |
| Address:                  [________________________________________]           |
| District:                 [Select District v]                                 |
|                                                                                |
| Preferred Language:       [English v]                                         |
|                                                                                |
|                                            [Save & Continue ->]                |
+--------------------------------------------------------------------------------+

2.2 Organization Profile
+--------------------------------------------------------------------------------+
| Step 1 of 7 — Organization Profile                                             |
+--------------------------------------------------------------------------------+
| Organization Name:       [City Hospital________________________]              |
| Organization Type:       [Hospital v]                                         |
| Organization Code:       [Auto-generated / editable if permitted]             |
| Contact Person:           [_______________________________]                  |
| Contact Mobile:           [_______________________________]                  |
| Email:                    [_______________________________]                  |
| Address:                  [_______________________________]                  |
|                                                                                |
| ORGANIZATION PREFERENCES                                                       |
| Default Language:         [বাংলা v]                                           |
| Timezone:                 [Asia/Dhaka v]                                      |
| Date Format:              [DD/MM/YYYY v]                                      |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

2.3 First Branch Setup
An organization may have multiple branches, but the first branch is required to begin operations.
+--------------------------------------------------------------------------------+
| Step 2 of 7 — Create First Branch                                              |
+--------------------------------------------------------------------------------+
| Branch Name:             [Main Branch____________________________]             |
| Branch Code:             [MAIN_______________________________]                 |
| Branch Contact:          [____________________________________]               |
| Mobile:                  [____________________________________]               |
| Address:                 [____________________________________]               |
| District:                [Select District v]                                  |
|                                                                                |
| BRANCH SETTINGS                                                                |
| Default Appointment Model: [Time-slot v]                                      |
| Queue Mode:                 [Enabled v]                                       |
|                                                                                |
| [x] This is the organization's primary branch                                 |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

The appointment model is configurable; the available models are time-slot, serial-based and hybrid.
2.4 Floor Setup
+--------------------------------------------------------------------------------+
| Step 3 of 7 — Facility Setup: Floors                                           |
+--------------------------------------------------------------------------------+
| Branch: Main Branch                                                            |
|                                                                                |
| FLOOR LIST                                                                     |
| +----------------------------------------------------------------------------+ |
| | Floor Code | Floor Name       | Description        | Rooms | Action       | |
| |------------|------------------|--------------------|-------|--------------| |
| | G          | Ground Floor     | Reception & OPD    | 8     | [Edit]       | |
| | 1          | First Floor      | Medicine           | 6     | [Edit]       | |
| | 2          | Second Floor     | Surgery             | 4     | [Edit]       | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [+ Add Floor]                                                                  |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

2.5 Room Setup
+--------------------------------------------------------------------------------+
| Step 3 of 7 — Facility Setup: Rooms                                            |
+--------------------------------------------------------------------------------+
| Select Floor: [Ground Floor v]                                                 |
|                                                                                |
| +----------------------------------------------------------------------------+ |
| | Room No. | Room Name        | Room Type        | Status   | Action         | |
| |----------|------------------|------------------|----------|----------------| |
| | G-101    | Chamber 1        | Doctor Chamber   | Active   | [Edit]         | |
| | G-102    | Chamber 2        | Doctor Chamber   | Active   | [Edit]         | |
| | G-103    | Consultation 3   | Doctor Chamber   | Active   | [Edit]         | |
| | G-104    | Diagnostic Room  | Other            | Active   | [Edit]         | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [+ Add Room]                                                                   |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

A room is a physical facility resource. Doctor assignment to a room is a separate operation.
2.6 First Organization Administrator
+--------------------------------------------------------------------------------+
| Step 4 of 7 — Organization Administrator                                       |
+--------------------------------------------------------------------------------+
| Administrator Name:       [____________________________________]              |
| Mobile Number:            [____________________________________]              |
| Email:                    [____________________________________]              |
|                                                                                |
| Login Credentials                                                             |
| Username:                 [____________________________________]              |
| Temporary Password:       [Generate Secure Password]                          |
|                                                                                |
| Role:                     ORGANIZATION ADMIN                                  |
|                                                                                |
| ACCESS                                                                         |
| [x] Organization-wide administration                                          |
| [x] Branch management                                                         |
| [x] Staff management                                                          |
| [x] Doctor management                                                         |
| [x] Organization settings                                                     |
|                                                                                |
| [ ] Platform administration (not permitted)                                  |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

The organization admin should receive a secure invitation or temporary credential flow. Never show stored passwords in the UI.
2.7 Add Doctors and Staff
+--------------------------------------------------------------------------------+
| Step 5 of 7 — Doctors & Staff                                                  |
+--------------------------------------------------------------------------------+
| [Add Doctor] [Add Staff]                                                       |
|                                                                                |
| DOCTORS                                                                        |
| +----------------------------------------------------------------------------+ |
| | Doctor Name      | Mobile          | Specialty      | Branch | Action      | |
| |------------------|-----------------|----------------|--------|-------------| |
| | Dr. Rahman       | +8801XXXXXXXXX  | Medicine       | Main   | [Edit]      | |
| | Dr. Karim        | +8801XXXXXXXXX  | Cardiology     | Main   | [Edit]      | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| STAFF                                                                          |
| +----------------------------------------------------------------------------+ |
| | Name             | Mobile          | Role          | Branch | Action      | |
| |------------------|-----------------|---------------|--------|-------------| |
| | Reception 1      | +8801XXXXXXXXX  | Receptionist  | Main   | [Edit]      | |
| | Assistant 1      | +8801XXXXXXXXX  | Assistant     | Main   | [Edit]      | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

A doctor profile and a staff login are separate concepts. The doctor may also be assigned a staff account with the doctor role.
2.8 Operations Configuration
+--------------------------------------------------------------------------------+
| Step 6 of 7 — Appointment & Queue Configuration                                |
+--------------------------------------------------------------------------------+
| APPOINTMENT DEFAULTS                                                           |
| Default Model:       (o) Time-slot  ( ) Serial-based  ( ) Hybrid                |
| Default Duration:   [15] minutes                                               |
|                                                                                |
| WALK-IN POLICY                                                                 |
| Walk-ins Enabled:    [x]                                                      |
| Walk-in Placement:   [End of queue v]                                          |
|                                                                                |
| QUEUE SETTINGS                                                                 |
| Manual Reordering:   [x]                                                      |
| Overbooking:         [ ] Disabled by default                                   |
| No-show Grace:       [15] minutes                                              |
|                                                                                |
| CANCELLATION                                                                   |
| Cancellation Reason Required: [x]                                             |
|                                                                                |
|                                     [Back] [Save & Continue]                   |
+--------------------------------------------------------------------------------+

These are defaults. Branch-level settings may override them only within organization and platform limits.
2.9 Review and Activate
+--------------------------------------------------------------------------------+
| Step 7 of 7 — Review Organization Setup                                        |
+--------------------------------------------------------------------------------+
| ORGANIZATION                                                                   |
| Name: City Hospital                                                            |
| Type: Hospital                                                                 |
| Contact: +8801XXXXXXXXX                                                        |
|                                                                                |
| BRANCHES                                                                       |
| 1. Main Branch                                                                 |
|                                                                                |
| FACILITY                                                                       |
| Floors: 3                         Rooms: 18                                    |
|                                                                                |
| USERS                                                                          |
| Organization Admin: 1             Doctors: 2       Staff: 2                    |
|                                                                                |
| OPERATIONS                                                                     |
| Appointment Model: Time-slot                                                  |
| Walk-ins: Enabled                 Overbooking: Disabled                       |
|                                                                                |
| SUBSCRIPTION                                                                   |
| Plan: Standard                     Status: Active                              |
|                                                                                |
| [ ] I confirm that the setup information is correct.                          |
|                                                                                |
| [Back]                                             [Complete Setup & Activate] |
+--------------------------------------------------------------------------------+

2.10 Onboarding Completion
+--------------------------------------------------------------------------------+
|                                                                                |
|                           ORGANIZATION READY                                  |
|                                                                                |
|                  City Hospital has been configured.                            |
|                                                                                |
|                  Organization ID: ORG-0001                                     |
|                  Primary Branch: Main Branch                                  |
|                  Organization Admin: Created                                  |
|                                                                                |
|                  [Open Organization Workspace]                                |
|                                                                                |
+--------------------------------------------------------------------------------+

3. Doctor Workspace
The Doctor Workspace is a focused operational interface. Doctors should not see platform administration or unrelated organization management.

Role: doctor

A doctor can access their own appointments, queue, assigned patients and schedule information according to the permissions granted by the organization.
3.1 Doctor Main Layout
+--------------------------------------------------------------------------------+
| AMSDP | Doctor Workspace                      Dr. Rahman       [Profile] [Exit]|
+--------------------------------------------------------------------------------+
| SIDEBAR                          | MAIN CONTENT                                |
|                                  |                                              |
| > My Dashboard                   |                                              |
|   My Appointments                |                                              |
|   My Queue                       |                                              |
|   My Schedule                    |                                              |
|   My Rooms / Sessions            |                                              |
|   My Patients                    |                                              |
|   Appointment History             |                                              |
|                                  |                                              |
+--------------------------------------------------------------------------------+

3.2 Doctor Dashboard
+--------------------------------------------------------------------------------+
| Good Morning, Dr. Rahman                         [Main Branch v] [06 Nov 2026] |
+--------------------------------------------------------------------------------+
| TODAY'S SUMMARY                                                                |
|                                                                                |
| TOTAL APPOINTMENTS      WAITING       IN CONSULTATION       COMPLETED          |
|       28                  9                  1                 12               |
|                                                                                |
| TODAY'S SESSION                                                                 |
| Status: ACTIVE                 Room: G-101                                     |
| Start: 09:00 AM                Expected End: 02:00 PM                           |
|                                                                                |
| [Open My Queue]                [View Schedule]                                 |
+--------------------------------------------------------------------------------+
| MY NEXT PATIENT                                                                |
|                                                                                |
| Token: 014                    Appointment: 11:45 AM                            |
| Patient: Patient Name        Status: Waiting                                  |
|                                                                                |
| [View Appointment]                                                              |
+--------------------------------------------------------------------------------+
| TODAY'S APPOINTMENTS                                                           |
| +----------------------------------------------------------------------------+ |
| | Token | Patient Name | Time      | Status          | Action               | |
| |-------|--------------|-----------|-----------------|----------------------| |
| | 012   | Patient A    | 11:15 AM  | Completed       | [View]               | |
| | 013   | Patient B    | 11:30 AM  | In Consultation | [View]               | |
| | 014   | Patient C    | 11:45 AM  | Waiting         | [View]               | |
| | 015   | Patient D    | 12:00 PM  | Booked          | [View]               | |
| +----------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+

Patient names are visible only to authorized staff. The public queue display must not reveal them.
3.3 My Appointments
+--------------------------------------------------------------------------------+
| My Appointments                                                                |
+--------------------------------------------------------------------------------+
| Date [06 Nov 2026] Status [All v] Search [Patient / Appointment ID_______]    |
+--------------------------------------------------------------------------------+
| Appointment ID | Token | Patient       | Time     | Status       | Action      |
|----------------|-------|---------------|----------|--------------|-------------|
| APT-1001       | 012   | Patient A      | 11:15 AM | Completed    | [View]      |
| APT-1002       | 013   | Patient B      | 11:30 AM | In Consult.  | [View]      |
| APT-1003       | 014   | Patient C      | 11:45 AM | Waiting      | [View]      |
| APT-1004       | 015   | Patient D      | 12:00 PM | Booked       | [View]      |
+--------------------------------------------------------------------------------+

Appointment details
+--------------------------------------------------------------------------------+
| Appointment Details: APT-1003                                                  |
+--------------------------------------------------------------------------------+
| Patient Information                                                            |
| Name: Patient C                                                                |
| Mobile: +8801XXXXXXXXX                                                         |
| Patient ID: PAT-00123                                                          |
|                                                                                |
| APPOINTMENT                                                                     |
| Doctor: Dr. Rahman                                                             |
| Branch: Main Branch                 Room: G-101                                |
| Date: 06 Nov 2026                  Time: 11:45 AM                               |
| Token: 014                         Queue Position: 3                           |
| Status: WAITING                                                               |
|                                                                                |
| QUEUE ACTIONS                                                                   |
| [Call Next] [Start Consultation] [Complete Appointment]                        |
|                                                                                |
| [Back to Appointments]                                                         |
+--------------------------------------------------------------------------------+

The Doctor Workspace should not contain clinical notes, prescriptions, vitals, or EMR functionality in the approved AMSDP scope.
3.4 My Queue
This is one of the doctor's most important operational screens.
+--------------------------------------------------------------------------------+
| My Queue — Dr. Rahman                                                          |
+--------------------------------------------------------------------------------+
| Branch: Main Branch v       Room: G-101       Session: ACTIVE                   |
|                                                                                |
| CURRENT TOKEN                                                                  |
|                                                                                |
|                              TOKEN 013                                         |
|                         [STARTED / IN CONSULTATION]                            |
|                                                                                |
|                           [Complete Consultation]                              |
+--------------------------------------------------------------------------------+
| QUEUE                                                                           |
| +----------------------------------------------------------------------------+ |
| | Position | Token | Appointment | Patient       | Status       | Action     | |
| |----------|-------|-------------|---------------|--------------|------------| |
| | 1        | 014   | 11:45 AM    | Patient C     | Waiting      | [Call]     | |
| | 2        | 015   | 12:00 PM    | Patient D     | Waiting      | [Call]     | |
| | 3        | 016   | 12:15 PM    | Patient E     | Booked       | [View]     | |
| | 4        | 017   | Walk-in     | Patient F     | Waiting      | [Call]     | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [Refresh Queue]                        [View Queue History]                   |
+--------------------------------------------------------------------------------+

Doctor queue actions
The available actions depend on the organization's permission configuration:
- Call a waiting patient.
- Start consultation.
- Complete appointment.
- Mark a patient as needing staff assistance, if that workflow is enabled.
- View appointment details.
- View queue history.
Manual reorder, cancellation, no-show and transfer permissions should be explicit rather than assumed.
3.5 Doctor Schedule
+--------------------------------------------------------------------------------+
| My Schedule                                                                    |
+--------------------------------------------------------------------------------+
| View: [Week v]     Branch: [Main Branch v]      [< Previous] [Next >]           |
+--------------------------------------------------------------------------------+
| TIME       | MON 09 | TUE 10 | WED 11 | THU 12 | FRI 13 | SAT 14               |
|------------|--------|--------|--------|--------|--------|----------------------|
| 09:00      | OPD    | OPD    | OPD    |        | OPD    | OPD                  |
| 10:00      | OPD    | OPD    | OPD    |        | OPD    | OPD                  |
| 11:00      | OPD    | OPD    | OPD    |        | OPD    | OPD                  |
| 12:00      | Break  | Break  | Break  |        | Break  | Break                |
| 01:00      | OPD    | OPD    | OPD    |        | OPD    | OPD                  |
+--------------------------------------------------------------------------------+
| [View Schedule Details]                                                        |
+--------------------------------------------------------------------------------+

Doctors can view their schedules. Editing schedules should be permission-controlled and normally managed by authorized organization or branch staff.
3.6 My Rooms and Sessions
+--------------------------------------------------------------------------------+
| My Rooms & Sessions                                                            |
+--------------------------------------------------------------------------------+
| BRANCH: Main Branch                                                            |
+--------------------------------------------------------------------------------+
| TODAY'S ROOM ASSIGNMENT                                                        |
| +----------------------------------------------------------------------------+ |
| | Session       | Room    | Time              | Status    | Action            | |
| |---------------|---------|-------------------|-----------|-------------------| |
| | Morning OPD   | G-101   | 09:00 - 02:00 PM   | Active    | [Open]            | |
| | Evening OPD   | G-103   | 05:00 - 08:00 PM   | Upcoming  | [View]            | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| CURRENT SESSION                                                               |
| Room: G-101                                                                   |
| Queue: Active                                                                 |
| [Open Queue]                                                                   |
+--------------------------------------------------------------------------------+

A doctor may have different rooms across sessions. Room assignments should have dates/times and preserve history when changed.
3.7 Doctor Session Control
+--------------------------------------------------------------------------------+
| Session Details — Morning OPD                                                 |
+--------------------------------------------------------------------------------+
| Doctor: Dr. Rahman                                                             |
| Branch: Main Branch                                                            |
| Room: G-101                                                                    |
| Start: 09:00 AM                   End: 02:00 PM                                 |
| Status: ACTIVE                                                                  |
|                                                                                |
| QUEUE STATUS                                                                   |
| Waiting: 9                       In Consultation: 1                             |
| Completed: 12                    Remaining: 10                                 |
|                                                                                |
| SESSION ACTIONS                                                                |
| [Pause Session] [Resume Session] [Request Room Change]                         |
|                                                                                |
| [Close Session]                                                                |
+--------------------------------------------------------------------------------+

Closing a session should trigger a confirmation if appointments remain. It must not automatically cancel or silently reschedule them.
3.8 My Patients
+--------------------------------------------------------------------------------+
| My Patients                                                                    |
+--------------------------------------------------------------------------------+
| Search [Patient name / mobile / ID________________________] [Search]           |
+--------------------------------------------------------------------------------+
| Patient ID | Patient Name | Mobile          | Last Appointment | Action        |
|------------|--------------|-----------------|------------------|---------------|
| PAT-00123  | Patient A    | +8801XXXXXXXXX  | 06 Nov 2026      | [View]        |
| PAT-00124  | Patient B    | +8801XXXXXXXXX  | 05 Nov 2026      | [View]        |
+--------------------------------------------------------------------------------+

Patient profile — Doctor view
+--------------------------------------------------------------------------------+
| Patient Profile                                                                |
+--------------------------------------------------------------------------------+
| Name: Patient A                                                                |
| Patient ID: PAT-00123                                                          |
| Mobile: +8801XXXXXXXXX                                                         |
|                                                                                |
| APPOINTMENT HISTORY WITH THIS DOCTOR                                           |
| +----------------------------------------------------------------------------+ |
| | Date       | Branch      | Token | Appointment Status | Action             | |
| |------------|-------------|-------|---------------------|--------------------| |
| | 06 Nov     | Main Branch | 012   | Completed           | [View]             | |
| | 20 Oct     | Main Branch | 021   | Completed           | [View]             | |
| +----------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+

Access to patient information must be limited to the doctor's authorized scope.
4. Assistant Workspace
The Assistant Workspace is designed around the assigned doctor, chamber and queue.

Role: assistant

The assistant is not automatically an organization administrator or receptionist. Their access is limited by the assigned doctor, branch and permissions.
4.1 Assistant Main Layout
+--------------------------------------------------------------------------------+
| AMSDP | Assistant Workspace                 Assistant Name      [Profile] [Exit]|
+--------------------------------------------------------------------------------+
| SIDEBAR                          | MAIN CONTENT                                |
|                                  |                                              |
| > My Dashboard                   |                                              |
|   Assigned Doctor                |                                              |
|   Chamber / Room                 |                                              |
|   Doctor Queue                   |                                              |
|   Today's Appointments            |                                              |
|   Walk-in Registration*           |                                              |
|   Queue History                  |                                              |
|                                  |                                              |
+--------------------------------------------------------------------------------+
| *Walk-in registration only if explicitly permitted.                           |
+--------------------------------------------------------------------------------+

4.2 Assistant Dashboard
+--------------------------------------------------------------------------------+
| Good Morning, Assistant                         [Main Branch v] [06 Nov 2026]  |
+--------------------------------------------------------------------------------+
| ASSIGNED DOCTOR                                                                |
| Dr. Rahman                                                                     |
| Specialty: Medicine                                                            |
| Room: G-101                                                                    |
| Session: Morning OPD                                                           |
| Status: ACTIVE                                                                  |
+--------------------------------------------------------------------------------+
| QUEUE SUMMARY                                                                  |
|                                                                                |
| WAITING             IN CONSULTATION           COMPLETED        NEXT TOKEN      |
|    9                       1                     12                014          |
+--------------------------------------------------------------------------------+
| CURRENT PATIENT                                                                |
| Token: 013                      Patient: Patient B                             |
| Status: In Consultation                                                         |
|                                                                                |
| [View Appointment]                                                             |
+--------------------------------------------------------------------------------+
| NEXT PATIENT                                                                   |
| Token: 014                      Patient: Patient C                             |
| Appointment: 11:45 AM                                                         |
|                                                                                |
| [View Patient]                 [Call Next Patient]                             |
+--------------------------------------------------------------------------------+
| QUICK ACTIONS                                                                  |
| [Open Doctor Queue] [Register Walk-in] [View Today's Appointments]             |
+--------------------------------------------------------------------------------+

4.3 Assigned Doctor
+--------------------------------------------------------------------------------+
| Assigned Doctor                                                                |
+--------------------------------------------------------------------------------+
| DOCTOR PROFILE                                                                 |
|                                                                                |
| Name: Dr. Rahman                                                               |
| Doctor ID: DOC-001                                                             |
| Specialty: Medicine                                                            |
| Branch: Main Branch                                                            |
|                                                                                |
| ASSIGNMENT DETAILS                                                             |
| Assigned Assistant: Assistant Name                                             |
| Effective From: 01 Nov 2026                                                    |
| Status: ACTIVE                                                                  |
|                                                                                |
| CURRENT SESSION                                                                |
| Room: G-101                                                                    |
| Session: Morning OPD                                                           |
| Start: 09:00 AM                   End: 02:00 PM                                 |
|                                                                                |
| [View Doctor Schedule]                                                         |
+--------------------------------------------------------------------------------+

The assistant should not be able to change their own doctor assignment unless a specific authorized workflow allows it.
4.4 Chamber / Room Overview
+--------------------------------------------------------------------------------+
| Chamber Overview                                                               |
+--------------------------------------------------------------------------------+
| Branch: Main Branch                                                            |
| Floor: Ground Floor                                                            |
| Room: G-101                                                                    |
| Doctor: Dr. Rahman                                                             |
| Session Status: ACTIVE                                                         |
+--------------------------------------------------------------------------------+
| CHAMBER QUEUE                                                                   |
|                                                                                |
| Current Token: 013                Next Token: 014                              |
| Waiting: 9                         Completed: 12                                |
|                                                                                |
| ROOM STATUS                                                                    |
| [Doctor Present] [Session Active] [Queue Active]                               |
|                                                                                |
| [Open Queue]                       [View Room Assignment History]              |
+--------------------------------------------------------------------------------+

Room reassignment should be performed by authorized staff or the doctor where permitted. The assistant should not silently move an appointment to a different room.
4.5 Doctor Queue — Assistant View
+--------------------------------------------------------------------------------+
| Doctor Queue — Dr. Rahman                                                     |
+--------------------------------------------------------------------------------+
| Branch: Main Branch       Room: G-101       Session: ACTIVE                    |
+--------------------------------------------------------------------------------+
| CURRENT CONSULTATION                                                          |
|                                                                                |
|                         TOKEN 013                                              |
|                         Patient B                                              |
|                         IN CONSULTATION                                        |
|                                                                                |
|                         [Notify Doctor]                                        |
+--------------------------------------------------------------------------------+
| WAITING QUEUE                                                                   |
| +----------------------------------------------------------------------------+ |
| | Position | Token | Appointment | Patient     | Status    | Action          | |
| |----------|-------|-------------|-------------|-----------|-----------------| |
| | 1        | 014   | 11:45 AM    | Patient C   | Waiting   | [Call]          | |
| | 2        | 015   | 12:00 PM    | Patient D   | Waiting   | [Call]          | |
| | 3        | 016   | 12:15 PM    | Patient E   | Booked    | [View]          | |
| | 4        | 017   | Walk-in     | Patient F   | Waiting   | [Call]          | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [Refresh] [View Queue History]                                                 |
+--------------------------------------------------------------------------------+

The assistant may call or prepare the next patient, but consultation start/completion authority should be defined by the permission matrix.
4.6 Today's Appointments
+--------------------------------------------------------------------------------+
| Today's Appointments — Dr. Rahman                                              |
+--------------------------------------------------------------------------------+
| Date: 06 Nov 2026             Status [All v]                                    |
+--------------------------------------------------------------------------------+
| Token | Patient Name | Time      | Status       | Action                       |
|-------|--------------|-----------|--------------|------------------------------|
| 012   | Patient A    | 11:15 AM  | Completed    | [View]                       |
| 013   | Patient B    | 11:30 AM  | In Consult.  | [View]                       |
| 014   | Patient C    | 11:45 AM  | Waiting      | [View]                       |
| 015   | Patient D    | 12:00 PM  | Booked       | [View]                       |
+--------------------------------------------------------------------------------+

4.7 Walk-in Registration
This screen is available only if the assistant has been granted the walk-in registration permission.
+--------------------------------------------------------------------------------+
| Register Walk-in                                                               |
+--------------------------------------------------------------------------------+
| ASSIGNED DOCTOR                                                                |
| Dr. Rahman                      Branch: Main Branch                            |
| Room: G-101                     Session: Morning OPD                            |
+--------------------------------------------------------------------------------+
| PATIENT SEARCH                                                                 |
| Mobile Number: [____________________________] [Search]                         |
|                                                                                |
| [Existing Patient Found]                                                       |
| Patient ID: PAT-00123                                                          |
| Name: Patient A                                                                |
|                                                                                |
| OR                                                                             |
| [Register New Patient]                                                         |
|                                                                                |
| PATIENT INFORMATION                                                            |
| Name: [________________________________________]                               |
| Mobile: [______________________________________]                               |
|                                                                                |
| WALK-IN DETAILS                                                                |
| Date: [06 Nov 2026]                                                            |
| Doctor: Dr. Rahman                                                             |
| Queue Placement: [End of queue v]                                              |
|                                                                                |
| [Cancel]                                           [Register Walk-in]           |
+--------------------------------------------------------------------------------+

Walk-in confirmation
+--------------------------------------------------------------------------------+
| WALK-IN REGISTERED                                                             |
+--------------------------------------------------------------------------------+
| Patient: Patient A                                                             |
| Appointment ID: APT-1045                                                       |
| Doctor: Dr. Rahman                                                             |
| Branch: Main Branch                                                            |
| Room: G-101                                                                    |
| Token: 018                                                                     |
| Queue Position: 5                                                              |
| Status: IN_QUEUE                                                               |
|                                                                                |
| [View Queue]                                    [Register Another Walk-in]     |
+--------------------------------------------------------------------------------+

The queue position is not an appointment time guarantee.
4.8 Call Next Patient
+--------------------------------------------------------------------------------+
| Call Next Patient                                                              |
+--------------------------------------------------------------------------------+
| Doctor: Dr. Rahman                                                             |
| Room: G-101                                                                    |
|                                                                                |
| NEXT PATIENT                                                                   |
|                                                                                |
|                         TOKEN 014                                              |
|                         Patient C                                               |
|                         Appointment: 11:45 AM                                  |
|                                                                                |
| [Confirm Call]                                [Cancel]                         |
+--------------------------------------------------------------------------------+

The action should be audited. It should not automatically change the appointment's time.
4.9 Queue History
+--------------------------------------------------------------------------------+
| Queue History — Dr. Rahman                                                    |
+--------------------------------------------------------------------------------+
| Date [06 Nov 2026] Token [All v] Action [All v] [Search]                       |
+--------------------------------------------------------------------------------+
| Time     | Token | Previous Position | New Position | Action       | Actor    |
|----------|-------|-------------------|--------------|--------------|----------|
| 11:10    | 014   | 2                 | 1            | Reordered    | Assistant|
| 11:15    | 012   | 1                 | -            | Completed    | Doctor   |
| 11:20    | 015   | 3                 | 2            | Reordered    | Assistant|
+--------------------------------------------------------------------------------+

The assistant can view history. Editing or deleting audit entries must not be possible.
5. Role-Based Workspace Access
The following matrix is the recommended starting point for these interfaces. Final permission assignment remains configurable by the appropriate administrator within platform limits.
Feature	Super Admin	Org Admin	Branch Admin	Receptionist	Doctor	Assistant
Platform dashboard	Yes	No	No	No	No	No
Organization onboarding	Yes	No	No	No	No	No
Subscription plans	Yes	No	No	No	No	No
Organization settings	No	Yes	Limited	No	No	No
Branch management	Oversight	Yes	Assigned	No	No	No
Floor/room management	Oversight	Yes	Assigned	Limited	View	View
Staff management	Platform users only	Yes	Assigned	No	No	No
Doctor management	Oversight	Yes	Assigned	View	Own profile	Assigned doctor
Patient registration	No	Configurable	Configurable	Yes	No by default	If permitted
Appointment booking	No	Configurable	Configurable	Yes	Limited	If permitted
Queue management	No	Configurable	Configurable	Yes	Own queue	Assigned queue
Doctor session	No	Configurable	Configurable	View	Own session	View / limited
Public display management	No	Yes	Assigned	View	No	No
Audit log	Platform audit	Org audit	Branch audit	No	Own relevant history	Own relevant history


"Yes" means the role may access the feature; actual operations must still be permission-checked.
6. Updated AMSDP Navigation Architecture
This is the consolidated navigation structure after adding the remaining workspaces.
AMSDP
|
+-- 1. PLATFORM CONTROL PLANE
|   |
|   +-- Platform Dashboard
|   +-- Organizations
|   +-- Onboarding Requests
|   +-- Branch Oversight
|   +-- Subscription Plans
|   +-- Subscriptions
|   +-- Platform Users
|   +-- Global Configuration
|   +-- System Monitoring
|   +-- Audit & Security
|   +-- Support Operations
|   +-- Platform Reports
|
+-- 2. ORGANIZATION WORKSPACE
|   |
|   +-- Organization Dashboard
|   +-- Organization Profile
|   +-- Branches
|   +-- Floors
|   +-- Rooms
|   +-- Staff & Permissions
|   +-- Doctors
|   +-- Patients
|   +-- Organization Settings
|   +-- Subscription Status
|   +-- Organization Audit
|
+-- 3. BRANCH OPERATIONS
|   |
|   +-- Branch Dashboard
|   +-- Today's Operations
|   +-- Appointments
|   +-- Walk-in Registration
|   +-- Queue Board
|   +-- Queue History
|   +-- Doctor Schedules
|   +-- Doctor-room Assignments
|   +-- Room Availability
|   +-- Patient Search
|   +-- Appointment Reschedule
|   +-- Cancellation / No-show
|
+-- 4. DOCTOR WORKSPACE
|   |
|   +-- My Dashboard
|   +-- My Appointments
|   +-- My Queue
|   +-- My Schedule
|   +-- My Rooms / Sessions
|   +-- My Patients
|   +-- Appointment History
|
+-- 5. ASSISTANT WORKSPACE
|   |
|   +-- My Dashboard
|   +-- Assigned Doctor
|   +-- Chamber / Room
|   +-- Doctor Queue
|   +-- Today's Appointments
|   +-- Walk-in Registration (permission-based)
|   +-- Queue History
|
+-- 6. PUBLIC DISPLAYS
    |
    +-- Floor-wide Display
    +-- Individual Chamber Display

7. MVP Implementation Priority
The UI blueprint is now complete at the screen-design level, but not every screen needs to be implemented before the first demonstrable MVP.
Priority	Area	Screens
P0	Platform Admin	Dashboard, organizations, onboarding review, subscription management
P0	Onboarding	Organization, branch, floor/room, first admin, initial staff/doctors, review
P0	Doctor	Dashboard, appointments, queue, session/room view
P0	Assistant	Dashboard, assigned doctor, queue, call next, appointment view
P0	Shared	Login, role-based navigation, permissions, branch context
P1	Platform Admin	Monitoring, reports, detailed audit, global configuration
P1	Onboarding	Bulk staff/doctor setup, advanced defaults
P1	Doctor	Schedule calendar, patient history, detailed queue history
P1	Assistant	Walk-in registration, room assignment history, detailed queue history


Important product decision before implementation: the Floor, Room, Doctor-Room Assignment and Doctor Session concepts are necessary for the chamber and floor-wide queue experience described in the UI designs. They should be formally added to the approved AMSDP domain model before AILI generates implementation tasks. The detailed permissions for doctors and assistants also need approval.
8. Recommended next artifact
The next step should be to consolidate all the existing and newly completed screens into one controlled AMSDP UI/UX Specification V1.0. It should include:
- Screen IDs and names.
- ASCII wireframes.
- Role access and permissions.
- Field definitions and validation.
- Buttons and their expected actions.
- Empty, loading, error and confirmation states.
- Navigation and screen-to-screen transitions.
- MVP versus later-phase classification.
- Explicit scope exclusions.

AMSDP should have analytics at three levels:
1. Platform Analytics — how the SaaS platform is performing.
2. Organization Analytics — how a hospital or clinic is performing across its branches.
3. Branch and User Analytics — how appointments, doctors, queues and daily operations are performing.
I would add this to the product blueprint before implementation.
1. Analytics architecture
Platform Analytics — Super Admin

Organizations · Subscriptions · Adoption · Platform health

Organization Analytics — Organization Admin

All branches · Doctors · Appointments · Queue performance

Branch Analytics

Branch Admin

Rooms · Doctors · Queues · Appointments

Personal Analytics

Doctor / Assistant

Own sessions · Queue · Appointment activity

Each level must enforce tenant and branch permissions. Platform Admin analytics should use aggregated operational data, not expose patient identities or contact information.
2. Platform Admin Analytics
Add a new sidebar item: Analytics & Reports.
2.1 Platform Overview
+--------------------------------------------------------------------------------+
| Platform Analytics                                  [Last 30 Days v] [Export]  |
+--------------------------------------------------------------------------------+
| TOTAL ORGANIZATIONS | ACTIVE ORGS | ACTIVE BRANCHES | ACTIVE STAFF             |
|        128          |     112     |       246       |     1,840                 |
+--------------------------------------------------------------------------------+
| NEW ORGANIZATIONS   | TRIAL CONVERSION | EXPIRED SUBSCRIPTIONS | SUSPENDED      |
|        12           |       68%        |          8            |      4         |
+--------------------------------------------------------------------------------+
| ORGANIZATION GROWTH                  SUBSCRIPTION DISTRIBUTION                  |
| +--------------------------------+  +---------------------------------------+ |
| |                                |  | Starter      Standard     Enterprise  | |
| |       [Line Chart]             |  | [Chart]                                | |
| |                                |  |                                       | |
| +--------------------------------+  +---------------------------------------+ |
|                                                                                |
| ORGANIZATIONS BY TYPE                                                         |
| +--------------------------------+  +---------------------------------------+ |
| | Hospital       45              |  | Onboarding Funnel                      | |
| | Clinic         53              |  | Submitted -> Approved -> Activated     | |
| | Diagnostic     30              |  |               [Funnel Chart]           | |
| +--------------------------------+  +---------------------------------------+ |
|                                                                                |
| PLATFORM ACTIVITY                                                             |
| [Organization registrations] [New branches] [New staff] [Subscription changes]|
+--------------------------------------------------------------------------------+

Additional platform analytics:
- Organization registration trends.
- Onboarding approval and rejection rates.
- Subscription activation, renewal and expiry trends.
- Trial-to-paid conversion, if trial and paid subscription states are implemented.
- Usage against plan limits.
- Active organizations and branches.
- Platform service availability and error trends.
Important: Do not introduce revenue, MRR, payment collection or financial ledger analytics. Those are outside the approved AMSDP scope. Subscription status and plan adoption are sufficient for this product.
3. Organization Admin Analytics
This is probably the most valuable analytics area for hospitals and clinics.

New navigation:
Organization Workspace
|
+-- Dashboard
+-- Analytics & Reports
|   |
|   +-- Organization Overview
|   +-- Appointment Analytics
|   +-- Queue Analytics
|   +-- Doctor Performance
|   +-- Branch Comparison
|   +-- Room Utilization
|   +-- Patient Activity
|   +-- Operational Reports
|
+-- Branches
+-- Doctors
+-- Patients
+-- Staff
+-- Settings

3.1 Organization Analytics Dashboard
+--------------------------------------------------------------------------------+
| Organization Analytics                       [Date Range v] [All Branches v]  |
+--------------------------------------------------------------------------------+
| TOTAL APPOINTMENTS | COMPLETED | CANCELLED | NO-SHOW | WALK-INS                |
|       4,820        |   3,940   |    320     |   180   |   760                   |
+--------------------------------------------------------------------------------+
| APPOINTMENT TRENDS                  APPOINTMENT STATUS                          |
| +--------------------------------+  +---------------------------------------+ |
| |                                |  | Completed      82%                     | |
| |        [Line Chart]            |  | Cancelled       7%                     | |
| |                                |  | No-show         4%                     | |
| |                                |  | Other           7%                     | |
| +--------------------------------+  +---------------------------------------+ |
|                                                                                |
| BRANCH PERFORMANCE                  DOCTOR ACTIVITY                             |
| +--------------------------------+  +---------------------------------------+ |
| | Branch      Appointments      |  | Doctor       Completed   Waiting         | |
| | Main        2,500             |  | Dr. Rahman      180         12           | |
| | North       1,420             |  | Dr. Karim       145          8           | |
| | South         900             |  | Dr. Sultana     130          9           | |
| +--------------------------------+  +---------------------------------------+ |
|                                                                                |
| QUEUE PERFORMANCE                                                              |
| Average Waiting Time: 24 min     Average Queue Length: 11                      |
| Longest Waiting Time: 68 min     Queue Completion Rate: 86%                    |
+--------------------------------------------------------------------------------+

Filters should include:
- Date range.
- Branch.
- Doctor.
- Appointment model.
- Appointment source (scheduled / walk-in).
- Appointment status.
3.2 Appointment Analytics
+--------------------------------------------------------------------------------+
| Appointment Analytics                         [Date Range v] [Branch v]       |
+--------------------------------------------------------------------------------+
| TOTAL BOOKINGS | COMPLETED | CANCELLED | NO-SHOW | RESCHEDULED                  |
|      850       |    690    |    55     |   30    |     75                      |
+--------------------------------------------------------------------------------+
| APPOINTMENTS BY DAY                                                            |
| +----------------------------------------------------------------------------+ |
| |                         [Daily Trend Chart]                               | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| APPOINTMENT SOURCE                                                             |
| +--------------------------------+                                             |
| | Scheduled: 72%                 |                                             |
| | Walk-in:    28%                |                                             |
| +--------------------------------+                                             |
|                                                                                |
| APPOINTMENT STATUS BY DAY                                                      |
| +----------------------------------------------------------------------------+ |
| | Date | Booked | Completed | Cancelled | No-show | Rescheduled              | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [Export Report]                                                               |
+--------------------------------------------------------------------------------+

Useful questions this analytics page answers:
- How many appointments were booked?
- How many were completed?
- What percentage were cancelled?
- How many patients did not attend?
- How many were rescheduled?
- How many patients came as walk-ins?
- Which days are busiest?
3.3 Queue Analytics
+--------------------------------------------------------------------------------+
| Queue Analytics                               [Date Range v] [Branch v]       |
+--------------------------------------------------------------------------------+
| AVERAGE WAIT | MAX WAIT | AVG QUEUE LENGTH | COMPLETION RATE                   |
|   24 min     | 68 min   |       11         |      86%                          |
+--------------------------------------------------------------------------------+
| WAITING TIME DISTRIBUTION                                                      |
| +----------------------------------------------------------------------------+ |
| | 0–15 min       [Chart]                                                     | |
| | 15–30 min      [Chart]                                                     | |
| | 30–60 min      [Chart]                                                     | |
| | Over 60 min    [Chart]                                                     | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| QUEUE BY HOUR                                                                  |
| +----------------------------------------------------------------------------+ |
| |                         [Hourly Activity Chart]                            | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| QUEUE BY DOCTOR                                                                |
| +----------------------------------------------------------------------------+ |
| | Doctor       | Avg Wait | Avg Queue | Completed |                           | |
| | Dr. Rahman   | 22 min   | 10        | 180       |                           | |
| | Dr. Karim    | 31 min   | 14        | 145       |                           | |
| +----------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+

A critical definition: waiting time should be calculated from the recorded check-in or queue-entry timestamp to the consultation-start timestamp, not from the scheduled appointment time.
3.4 Doctor Performance Analytics
+--------------------------------------------------------------------------------+
| Doctor Analytics                              [Date Range v] [Branch v]       |
+--------------------------------------------------------------------------------+
| DOCTOR: [All Doctors v]                                                       |
+--------------------------------------------------------------------------------+
| Doctor        | Booked | Completed | Cancelled | No-show | Avg Wait             |
|---------------|--------|-----------|-----------|---------|----------------------|
| Dr. Rahman    | 220    | 180       | 15        | 8       | 22 min               |
| Dr. Karim     | 190    | 145       | 12        | 10      | 31 min               |
| Dr. Sultana   | 160    | 130       | 8         | 5       | 18 min               |
+--------------------------------------------------------------------------------+
| APPOINTMENTS PER DOCTOR               COMPLETION TREND                         |
| +--------------------------------+    +------------------------------------+  |
| |        [Bar Chart]             |    |          [Line Chart]              |  |
| +--------------------------------+    +------------------------------------+  |
+--------------------------------------------------------------------------------+

Avoid presenting these metrics as a simplistic doctor quality or clinical performance ranking. Appointment volume and waiting time are operational indicators, not measures of medical quality.
3.5 Branch Comparison
+--------------------------------------------------------------------------------+
| Branch Comparison                              [Date Range v]                  |
+--------------------------------------------------------------------------------+
| Metric                  | Main Branch | North Branch | South Branch             |
|-------------------------|-------------|--------------|--------------------------|
| Appointments            | 2,500       | 1,420        | 900                      |
| Completed               | 2,100       | 1,150        | 690                      |
| Cancelled               | 150         | 90           | 80                       |
| No-show                 | 90          | 50           | 40                       |
| Walk-ins                | 420         | 210          | 130                      |
| Average Wait            | 22 min      | 28 min       | 25 min                   |
+--------------------------------------------------------------------------------+
| APPOINTMENT VOLUME BY BRANCH                                                   |
| +----------------------------------------------------------------------------+ |
| |                             [Comparison Chart]                             | |
| +----------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+

3.6 Room Utilization
This becomes particularly useful for hospitals with multiple floors and chambers.
+--------------------------------------------------------------------------------+
| Room Utilization                                [Date Range v] [Branch v]      |
+--------------------------------------------------------------------------------+
| Floor: [All v]                     Room Type: [All v]                          |
+--------------------------------------------------------------------------------+
| Floor       | Room  | Sessions | Assigned Doctors | Utilization                |
|-------------|-------|----------|------------------|----------------------------|
| Ground      | G-101 | 24       | 3                | 82%                        |
| Ground      | G-102 | 20       | 2                | 70%                        |
| First       | 1-101 | 28       | 4                | 91%                        |
| Second      | 2-101 | 12       | 2                | 45%                        |
+--------------------------------------------------------------------------------+
| ROOM UTILIZATION BY TIME                                                       |
| +----------------------------------------------------------------------------+ |
| |                              [Heatmap]                                     | |
| +----------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+

Room utilization should be calculated using actual assigned/active session time against the room's configured available time. It must not assume a room was occupied merely because an appointment was booked.
4. Branch Admin Analytics
Branch Admin needs more operationally focused reports.
Report	Purpose
Today's appointments	Current workload
Appointment completion	Operational completion rate
Walk-in activity	Walk-in volume and placement
Queue waiting time	Identify delays
Doctor activity	Doctor session and appointment workload
Room utilization	Identify chamber usage patterns
No-show and cancellation	Identify scheduling problems
Peak-hour activity	Plan staffing and room allocation


The Branch Admin dashboard can contain the most important metrics, with detailed reports under Analytics & Reports.
5. Doctor Analytics
Doctors should have personal analytics, not organization-wide analytics.
My Performance
+--------------------------------------------------------------------------------+
| My Analytics — Dr. Rahman                     [Last 30 Days v]                  |
+--------------------------------------------------------------------------------+
| TOTAL APPOINTMENTS | COMPLETED | CANCELLED | NO-SHOW | AVG WAIT                  |
|       420          |    350    |    28     |   16    | 22 min                   |
+--------------------------------------------------------------------------------+
| MY APPOINTMENTS BY DAY                                                        |
| +----------------------------------------------------------------------------+ |
| |                            [Line Chart]                                   | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| MY QUEUE PERFORMANCE                                                           |
| Average Waiting Time: 22 min                                                   |
| Average Daily Patients: 14                                                     |
| Average Queue Completion: 90%                                                 |
|                                                                                |
| SESSION SUMMARY                                                               |
| Sessions Completed: 24                                                        |
| Sessions Paused: 2                                                            |
+--------------------------------------------------------------------------------+

Doctors should see their own records and authorized operational statistics only.
6. Assistant Analytics
Assistants need fewer analytics than doctors and administrators.
+--------------------------------------------------------------------------------+
| My Operational Summary                         [Last 7 Days v]                 |
+--------------------------------------------------------------------------------+
| QUEUE ACTIONS | WALK-INS REGISTERED | PATIENTS CALLED | ACTIVE SESSIONS         |
|      180      |         24          |       150       |        12               |
+--------------------------------------------------------------------------------+
| DAILY ACTIVITY                                                                |
| +----------------------------------------------------------------------------+ |
| |                            [Activity Chart]                                | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| QUEUE OPERATIONS                                                               |
| Reorder Actions: 12                                                           |
| Walk-in Registrations: 24                                                    |
| Doctor Assignments: Assigned Doctor Only                                     |
+--------------------------------------------------------------------------------+

These are activity counts, not employee performance scores. The purpose is operational visibility.
7. Other Gaps I Recommend Addressing
Analytics is one gap. I see several other areas worth adding to the full specification.
Gap	Why it matters	Priority
Analytics and reporting	Understand appointment and queue performance	P0
Notification centre	Show operational alerts to staff	P0
In-app alerts	Notify of schedule changes, queue delays and session changes	P0
Data export	Export authorized operational reports	P1
Audit viewer	Understand who changed appointments and queue positions	P0
Bulk import	Import existing doctors, patients and staff	P1
Organization onboarding checklist	Prevent incomplete setup	P0
Doctor availability calendar	Avoid schedule conflicts	P0
Room availability	Avoid assigning multiple active sessions to the same room	P0
Display health monitoring	Detect disconnected public queue displays	P1
Backup and recovery visibility	Give admins confidence in data protection	P1
Accessibility and responsive UX	Usable on reception desktops, tablets and phones	P0
Error and empty states	Prevent confusing or unusable screens	P0
Data retention and privacy controls	Protect tenant and patient data	P0
Subscription usage alerts	Warn organizations approaching limits	P1


8. Important: Analytics Requires Data Model Support
This is the biggest technical point.

We cannot build reliable analytics just by putting charts on the dashboard. AMSDP must capture the underlying operational events consistently.

I recommend these records and timestamps:
Event / record	Analytics supported
Appointment created	Booking trends
Appointment source	Scheduled vs walk-in
Check-in timestamp	Waiting-time measurement
Queue-entry timestamp	Queue performance
Queue position changes	Queue movement analysis
Consultation started	Actual waiting time
Appointment completed	Completion statistics
Cancellation timestamp and reason	Cancellation analysis
No-show confirmation	No-show reporting
Reschedule linkage	Rescheduling analysis
Session start/end/pause	Doctor session analytics
Room assignment history	Room utilization
Actor and action history	Staff activity and audit


All timestamps should be stored consistently, ideally in UTC, and displayed using the organization's timezone.

Analytics definitions must also be fixed. For example, the denominator for a completion rate should be explicitly defined, and cancelled, rescheduled and no-show appointments should not be accidentally counted as completed or active.
9. Recommended final analytics scope
AMSDP Analytics — Proposed Scope
(Recommended P0)

Platform Admin
- Organization growth and adoption
- Onboarding funnel
- Subscription status and usage
- Platform health
Organization Admin
- Appointment analytics
- Queue analytics
- Doctor operational activity
- Branch comparison
- Room utilization
Branch Admin
- Daily operations
- Appointment completion
- Queue waiting times
- Walk-in and no-show activity
- Doctor and room workload
Doctor
- Personal appointment trends
- Queue performance
- Session summaries
Assistant
- Queue activity
- Walk-in registration activity, if permitted
- Session operations
My recommendation is to make Analytics & Reports a first-class module, not just a collection of dashboard charts.

# AMSDP Analytics Specification V1.0

**Product:** Appointment Management System for Doctors & Patients (AMSDP)  
**Document Type:** Product and Technical Specification  
**Status:** Proposed — requires product-owner approval  
**Version:** 1.0  
**Date:** 6 November 2026

---

## 1. Purpose

The AMSDP Analytics module provides operational insights to platform administrators, healthcare organizations, branches, doctors and assistants.

It supports:

- SaaS platform oversight.
- Organization and branch operations.
- Appointment and queue performance.
- Doctor workload visibility.
- Room and session utilization.
- Walk-in and attendance analysis.
- Authorized staff activity reporting.

Analytics must be tenant-isolated, branch-scoped, permission-controlled and based on auditable operational events.

### 1.1 Design principles

1. Every metric must have a documented formula.
2. Every metric must identify its source events.
3. Every metric must define its reporting period and timezone.
4. Analytics must respect organization and branch boundaries.
5. Personal analytics must not expose other users' restricted information.
6. Public displays must not expose analytics or patient information.
7. Historical reports must remain consistent when appointments are rescheduled or transferred.
8. Corrections to source records must be traceable.
9. Missing or insufficient data must be displayed as unavailable, not silently interpreted as zero.
10. Analytics must not imply clinical quality or medical outcomes.

---

# 2. Analytics Architecture

AMSDP analytics is divided into five access levels.

| Level | User role | Scope |
|---|---|---|
| Platform | super_admin | Aggregated platform-wide information |
| Organization | org_admin | All authorized branches within one organization |
| Branch | branch_admin | Assigned branch or branches |
| Personal | doctor | Own appointments, sessions and queue |
| Operational | assistant | Assigned doctor, branch, room and permitted activities |

Receptionists use operational dashboards and appointment reports within their authorized branch scope.

### 2.1 Data isolation

Every organization-owned analytics query must be scoped by organization ID.

Branch-level reports must additionally enforce branch access.

Doctor reports must enforce the authenticated doctor's identity unless an authorized administrator is viewing the report.

Assistant reports must enforce the assistant's assigned doctor and permitted branch scope.

Platform analytics must use aggregated data and must not reveal patient identities, phone numbers or appointment-level patient details.

### 2.2 Analytics data flow

```text
Appointment Operations
        |
Queue Operations
        |
Doctor Sessions
        |
Room Assignments
        |
Organization / Branch Management
        |
        v
Operational Event Records
        |
        v
Analytics Aggregation Layer
        |
        +-------------------------------+
        |                               |
        v                               v
Platform Analytics              Tenant Analytics
        |                               |
        v                               v
Super Admin Dashboard       Organization / Branch Reports
                                        |
                              +---------+---------+
                              |                   |
                              v                   v
                       Doctor Analytics    Assistant Analytics
```

The analytics aggregation layer must not bypass the application's authorization and tenant-isolation rules.

---

# 3. Common Reporting Rules

## 3.1 Date and time

- Store event timestamps in UTC.
- Display timestamps in the organization's configured timezone.
- Default organization timezone for Bangladesh deployments: Asia/Dhaka, configurable where necessary.
- Date filters refer to local calendar dates in the reporting organization's timezone.
- Date ranges are inclusive of the selected start date and end date.
- Use consistent half-open timestamp intervals internally: start inclusive, next-day-after-end exclusive.

Example:

A report for 6 November 2026 in Dhaka includes events from local midnight on 6 November up to, but not including, local midnight on 7 November.

## 3.2 Default date filters

| Filter | Meaning |
|---|---|
| Today | Current local calendar day |
| Yesterday | Previous local calendar day |
| Last 7 days | Previous seven calendar days, including today |
| Last 30 days | Previous thirty calendar days, including today |
| This week | Current calendar week |
| This month | Current calendar month |
| Custom | User-selected start and end dates |

## 3.3 Common filters

| Filter | Availability |
|---|---|
| Date range | All analytics modules |
| Organization | Platform Admin only |
| Branch | Organization and Branch Admin, authorized staff |
| Doctor | Organization and Branch Admin; personal scope for doctor/assistant |
| Floor | Facility analytics |
| Room | Facility analytics |
| Appointment model | Appointment analytics |
| Appointment source | Appointment analytics |
| Appointment status | Appointment analytics |
| Session | Doctor and room analytics |
| Walk-in | Appointment and queue analytics |

Filters must not allow a user to select an organization or branch outside their authorized scope.

## 3.4 Common metric presentation

Every metric should include:

- Metric name.
- Current value.
- Reporting period.
- Comparison period, if available.
- Unit.
- Tooltip explaining the definition.
- Data freshness or last-updated timestamp.

Do not show percentage changes when the comparison-period denominator is zero or unavailable.

---

# 4. Metric Dictionary

All formulas below are proposed canonical definitions. They must be implemented consistently by backend aggregation services and frontend reports.

## 4.1 Platform Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| PL-001 | Total organizations | Count of organization records excluding deleted records | OrganizationCreated, OrganizationStatusChanged |
| PL-002 | Active organizations | Count of organizations with active status | OrganizationStatusChanged |
| PL-003 | Suspended organizations | Count of organizations with suspended status | OrganizationStatusChanged |
| PL-004 | Active branches | Count of active branches belonging to active organizations | BranchCreated, BranchStatusChanged, OrganizationStatusChanged |
| PL-005 | Active staff | Count of enabled staff accounts that are not deactivated | StaffCreated, StaffStatusChanged |
| PL-006 | New organizations | Count of organizations created during the reporting period | OrganizationCreated |
| PL-007 | New branches | Count of branches created during the reporting period | BranchCreated |
| PL-008 | Onboarding approval rate | Approved onboarding requests / decided onboarding requests × 100 | OnboardingApproved, OnboardingRejected |
| PL-009 | Onboarding completion rate | Completed onboarding setups / approved onboarding setups × 100 | OnboardingCompleted |
| PL-010 | Trial conversion rate | Trials that enter the defined converted state / trials eligible for conversion × 100 | SubscriptionStatusChanged |
| PL-011 | Expiring subscriptions | Count of active subscriptions whose expiry date falls within the selected horizon | SubscriptionCreated, SubscriptionChanged |
| PL-012 | Plan distribution | Count of organizations grouped by current subscription plan | SubscriptionPlanChanged |
| PL-013 | Plan limit utilization | Current usage / configured plan limit × 100 | Organization, Branch and Staff records |
| PL-014 | Platform service availability | Available monitoring intervals / total valid monitoring intervals × 100 | ServiceHealthRecorded |

**Important definitions:**

- Onboarding approval rate excludes pending requests from the denominator.
- Onboarding completion rate uses approved onboarding setups as its denominator.
- Trial conversion requires a clearly defined subscription transition. A manually created paid subscription must not automatically be counted as a trial conversion.
- Plan limit utilization is calculated independently for each limit.
- Service availability requires monitoring records and a defined measurement interval.

## 4.2 Appointment Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| AP-001 | Appointments created | Count of appointments initially created in the reporting period | AppointmentCreated |
| AP-002 | Booked appointments | Count of appointments currently in BOOKED status | AppointmentStatusChanged |
| AP-003 | Confirmed appointments | Count of appointments currently in CONFIRMED status | AppointmentStatusChanged |
| AP-004 | Completed appointments | Count of appointments with completed status | AppointmentCompleted |
| AP-005 | Cancelled appointments | Count of appointments cancelled during the reporting period | AppointmentCancelled |
| AP-006 | No-show appointments | Count of appointments confirmed as no-show during the reporting period | AppointmentNoShowConfirmed |
| AP-007 | Rescheduled appointments | Count of original appointments linked to a rescheduled replacement | AppointmentRescheduled |
| AP-008 | Walk-in appointments | Count of appointments created with walk-in source | WalkInRegistered |
| AP-009 | Scheduled appointment share | Scheduled-source appointments / all appointments created × 100 | AppointmentCreated |
| AP-010 | Walk-in share | Walk-in-source appointments / all appointments created × 100 | WalkInRegistered, AppointmentCreated |
| AP-011 | Completion rate | Completed appointments / eligible appointments × 100 | AppointmentCompleted and appointment lifecycle events |
| AP-012 | Cancellation rate | Cancelled appointments / eligible appointments × 100 | AppointmentCancelled and appointment lifecycle events |
| AP-013 | No-show rate | Confirmed no-shows / eligible appointments × 100 | AppointmentNoShowConfirmed |
| AP-014 | Reschedule rate | Original appointments rescheduled / eligible appointments × 100 | AppointmentRescheduled |

### Appointment denominator rules

For AP-011 through AP-014:

Eligible appointments are appointments whose scheduled operating date falls within the selected reporting period and whose final disposition is known.

Exclude:

- Appointments still awaiting a final outcome.
- Original appointments marked RESCHEDULED when counting completed/cancelled/no-show outcomes for the replacement appointment.
- Test or explicitly voided records.

A rescheduled appointment must retain its original record and linked replacement record. Reports must distinguish:

1. Booking creation activity.
2. Scheduled appointment demand.
3. Final appointment outcomes.

Do not count a reschedule as both a cancellation and a completed appointment.

For operational outcome reporting, assign the final disposition to the appointment instance that actually took place or was cancelled/no-show.

## 4.3 Queue Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| QU-001 | Average waiting time | Sum of valid wait durations / number of valid consultations started | QueueEntered, ConsultationStarted |
| QU-002 | Maximum waiting time | Maximum valid waiting duration in the period | QueueEntered, ConsultationStarted |
| QU-003 | Average queue length | Average number of eligible waiting entries across sampled queue observations | QueueSnapshotRecorded |
| QU-004 | Queue completion rate | Completed queue entries / eligible queue entries × 100 | QueueEntered, AppointmentCompleted |
| QU-005 | Average daily queue volume | Total queue entries / number of days with recorded queue activity | QueueEntered |
| QU-006 | Average queue position | Sum of recorded queue positions / number of valid position observations | QueuePositionChanged, QueueSnapshotRecorded |
| QU-007 | Reorder count | Number of valid manual queue reorder actions | QueuePositionChanged |
| QU-008 | Queue delay count | Number of queue entries exceeding the configured waiting-time threshold | QueueEntered, QueueSnapshotRecorded, ConsultationStarted |
| QU-009 | Waiting-time distribution | Count of valid waiting durations grouped into defined ranges | QueueEntered, ConsultationStarted |
| QU-010 | Queue activity by hour | Count of queue-entry events grouped by local hour | QueueEntered |

### Waiting-time formula

For a queue entry that reaches consultation:

`Waiting time = consultation_started_at - queue_entered_at`

Use the earliest valid queue-entry timestamp for the active queue instance.

Do not use scheduled appointment time as the waiting-time start.

Do not include:

- Appointments that never entered the queue.
- Cancelled appointments that never started consultation.
- Invalid or incomplete timestamp sequences.

For an appointment that re-enters a queue after a formally recorded transfer or new queue instance, use the appropriate queue-instance ID. Do not combine separate queue visits into one waiting interval without an explicit metric definition.

### Queue length formula

`Average queue length = sum of sampled waiting-queue counts / number of valid samples`

Use periodic snapshots or another documented sampling strategy.

Do not calculate average queue length from the final queue position or from the total number of appointments booked.

### Queue completion formula

`Queue completion rate = completed queue entries / eligible queue entries × 100`

Eligible entries must have reached a defined queue state and have a final disposition. Report pending entries separately.

## 4.4 Doctor Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| DR-001 | Doctor appointment volume | Count of appointment instances assigned to the doctor | AppointmentCreated, AppointmentDoctorAssigned |
| DR-002 | Completed appointments | Count of appointments completed by the doctor | AppointmentCompleted |
| DR-003 | Average daily appointments | Doctor appointment volume / active reporting days | AppointmentCreated |
| DR-004 | Average waiting time | Average valid queue wait for the doctor's consultation entries | QueueEntered, ConsultationStarted |
| DR-005 | Session count | Count of doctor sessions started | DoctorSessionStarted |
| DR-006 | Completed sessions | Count of sessions with a recorded end/close event | DoctorSessionClosed |
| DR-007 | Active session duration | Sum of valid active session intervals | DoctorSessionStarted, DoctorSessionPaused, DoctorSessionResumed, DoctorSessionClosed |
| DR-008 | Session pause count | Count of recorded session pause events | DoctorSessionPaused |
| DR-009 | Doctor queue completion rate | Completed queue entries / eligible queue entries × 100 | Queue and appointment events |

These are workload and operational indicators. They must not be described as clinical quality, patient satisfaction or medical effectiveness scores.

## 4.5 Room Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| RM-001 | Room session count | Count of sessions assigned to the room | RoomSessionAssigned |
| RM-002 | Room assigned duration | Sum of valid assigned session intervals | RoomSessionAssigned, RoomSessionReleased |
| RM-003 | Room active duration | Sum of valid intervals during which the assigned session is active | DoctorSessionStarted, DoctorSessionPaused, DoctorSessionResumed, DoctorSessionClosed |
| RM-004 | Room utilization | Active room duration / configured available room duration × 100 | RoomAvailabilityConfigured and session events |
| RM-005 | Room conflict count | Count of prevented or recorded overlapping assignment conflicts | RoomAssignmentConflictDetected |
| RM-006 | Room reassignment count | Count of room assignment changes | RoomSessionReassigned |

Room utilization must not be inferred from appointment volume.

A room with appointments booked but no active session is not automatically considered occupied.

## 4.6 Assistant Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| AS-001 | Queue actions | Count of permitted queue actions performed by the assistant | QueueActionPerformed |
| AS-002 | Walk-ins registered | Count of walk-in appointments registered by the assistant | WalkInRegistered |
| AS-003 | Patients called | Count of successful patient-call actions | QueuePatientCalled |
| AS-004 | Queue reorder actions | Count of successful manual reorder actions | QueuePositionChanged |
| AS-005 | Session support activity | Count of recorded assistant actions associated with assigned sessions | SessionActionRecorded |

These metrics are for personal operational visibility, not employee ranking or disciplinary scoring.

## 4.7 Patient Activity Metrics

| ID | Metric | Definition and formula | Source events |
|---|---|---|---|
| PA-001 | New patient registrations | Count of patient records created during the period | PatientCreated |
| PA-002 | Patients with appointments | Distinct patients with an eligible appointment in the period | AppointmentCreated |
| PA-003 | Returning patients | Distinct patients with more than one eligible appointment across their recorded history | AppointmentCreated |
| PA-004 | Duplicate warnings | Count of duplicate-patient warnings generated | PatientDuplicateWarningRaised |
| PA-005 | Authorized merges | Count of authorized patient merges | PatientMerged |

Patient analytics must be restricted to the authorized organization. Patient mobile numbers and names must not be included in platform-wide reports.

---

# 5. Event Source Specification

Analytics must use reliable operational event records.

An event should be append-only. Corrections should create additional events or controlled correction records rather than silently rewriting historical activity.

## 5.1 Common event fields

Every event should contain:

| Field | Purpose |
|---|---|
| event_id | Unique event identifier |
| event_type | Event name |
| organization_id | Tenant boundary |
| branch_id | Branch scope, nullable for platform-level events |
| actor_user_id | Authenticated actor, nullable for system events |
| subject_type | Appointment, queue, doctor, room, etc. |
| subject_id | Identifier of the affected record |
| occurred_at | Actual event time in UTC |
| recorded_at | Time event was persisted |
| correlation_id | Links related operations |
| causation_id | Identifies the preceding event, where applicable |
| metadata | Approved structured event details |
| schema_version | Event schema version |

Do not store unnecessary patient personal information in analytics event metadata.

## 5.2 Required event catalogue

### Organization and platform events

- OrganizationCreated
- OrganizationStatusChanged
- OnboardingSubmitted
- OnboardingApproved
- OnboardingRejected
- OnboardingCompleted
- BranchCreated
- BranchStatusChanged
- SubscriptionCreated
- SubscriptionStatusChanged
- SubscriptionPlanChanged
- StaffCreated
- StaffStatusChanged
- ServiceHealthRecorded

### Patient events

- PatientCreated
- PatientDuplicateWarningRaised
- PatientMerged

### Appointment events

- AppointmentCreated
- AppointmentConfirmed
- AppointmentCheckedIn
- AppointmentStatusChanged
- AppointmentCancelled
- AppointmentNoShowConfirmed
- AppointmentRescheduled
- AppointmentTransferred
- AppointmentDoctorAssigned

### Queue events

- QueueEntered
- QueuePositionChanged
- QueuePatientCalled
- QueuePatientRecalled
- QueueTransferred
- ConsultationStarted
- AppointmentCompleted
- QueueSnapshotRecorded

### Session and room events

- DoctorSessionAssigned
- DoctorSessionStarted
- DoctorSessionPaused
- DoctorSessionResumed
- DoctorSessionClosed
- RoomSessionAssigned
- RoomSessionReassigned
- RoomSessionReleased
- RoomAvailabilityConfigured
- RoomAssignmentConflictDetected

### Assistant activity events

- QueueActionPerformed
- WalkInRegistered
- SessionActionRecorded

## 5.3 Event correctness requirements

1. Event creation must be part of the same reliable transaction as the business operation, or use a transactional outbox.
2. Event consumers must be idempotent.
3. Event IDs must be unique.
4. Event ordering must be handled using timestamps and causal relationships where necessary.
5. Failed business operations must not produce successful-operation events.
6. Queue reorder events must include previous and new positions.
7. Rescheduling must link the original and replacement appointments.
8. Transfers must preserve source and destination branch references.
9. Session pause/resume intervals must be recorded.
10. Event schema changes must be versioned.

---

# 6. Role Permissions

The following matrix is the proposed default. It must be implemented through server-side authorization, not frontend visibility alone.

| Analytics feature | super_admin | org_admin | branch_admin | receptionist | doctor | assistant |
|---|---|---|---|---|---|---|
| Platform analytics | Full | No | No | No | No | No |
| Organization overview | Aggregate only | Full | Assigned branches | Limited operational | No | No |
| Appointment analytics | Aggregate only | Full | Assigned branches | Authorized branch | Own appointments | Assigned doctor |
| Queue analytics | Aggregate only | Full | Assigned branches | Authorized branch | Own queue | Assigned queue |
| Doctor analytics | Aggregate only | Full | Assigned branches | Limited | Own metrics | Assigned doctor, if permitted |
| Branch comparison | Aggregate only | Full | Assigned branches | No by default | No | No |
| Room utilization | Aggregate only | Full | Assigned branches | Limited | Assigned rooms | Assigned rooms |
| Patient activity | Aggregate only | Full, controlled | Assigned branches | Authorized branch | Authorized own-patient scope | Only if permitted |
| Assistant activity | Aggregate only | Full | Assigned branches | No | No | Own activity |
| Export analytics | Platform aggregate | Organization scope | Assigned branch scope | Explicit permission | Own scope | Own permitted scope |
| Audit analytics events | Platform audit | Organization audit | Branch audit | No | Own relevant history | Own relevant history |

### 6.1 Platform Admin

May see:

- Organization and branch counts.
- Subscription states and plan usage.
- Onboarding funnel.
- Aggregated platform usage.
- Platform service monitoring.

Must not see patient-level details through analytics.

### 6.2 Organization Admin

May see all authorized branches belonging to the same organization.

Must not access another organization's operational data.

### 6.3 Branch Admin

May see only assigned branch or branches.

### 6.4 Receptionist

May see appointment and queue reports required for branch operations, subject to permission settings.

### 6.5 Doctor

May see own appointments, sessions and queue performance.

### 6.6 Assistant

May see assigned doctor and queue activity.

Personal activity counts must not be used as an automatic employee performance rating.

---

# 7. Filter Specification

| Filter | Platform | Organization | Branch | Doctor | Assistant |
|---|---|---|---|---|---|
| Date range | Yes | Yes | Yes | Yes | Yes |
| Organization | Yes | Fixed | Fixed | Fixed | Fixed |
| Branch | Yes | Authorized branches | Assigned | Assigned | Assigned |
| Doctor | Yes, aggregate | Authorized doctors | Authorized doctors | Own doctor | Assigned doctor |
| Floor | Where available | Yes | Yes | Assigned scope | Assigned scope |
| Room | Where available | Yes | Yes | Assigned scope | Assigned scope |
| Appointment status | No | Yes | Yes | Own scope | Assigned scope |
| Appointment source | No | Yes | Yes | Own scope | Assigned scope |
| Appointment model | No | Yes | Yes | Own scope | Assigned scope |
| Session | No | Yes | Yes | Own sessions | Assigned sessions |

### Filter behavior

- Changing a filter must refresh all dependent metrics and charts.
- Filters must be validated server-side.
- Unsupported combinations must be rejected or disabled.
- Empty result sets must display a clear empty state.
- Filters should be reflected in the report title and export metadata.
- Date-range changes must not silently change the selected branch or doctor.

---

# 8. ASCII UI Wireframes

## 8.1 Platform Admin Analytics

```text
+--------------------------------------------------------------------------------+
| AMSDP PLATFORM / ANALYTICS                         [Last 30 Days v] [Export]   |
+--------------------------------------------------------------------------------+
| ORGANIZATIONS | ACTIVE ORGS | ACTIVE BRANCHES | ACTIVE STAFF                  |
|      128      |     112     |       246       |     1,840                      |
+--------------------------------------------------------------------------------+
| NEW ORGANIZATIONS | ONBOARDING APPROVAL | EXPIRING | SUSPENDED                 |
|        12         |        84%           |    5     |     4                     |
+--------------------------------------------------------------------------------+
| ORGANIZATION GROWTH                SUBSCRIPTION DISTRIBUTION                    |
| +------------------------------+   +----------------------------------------+ |
| |                              |   | Starter / Standard / Enterprise        | |
| |        [Line Chart]          |   |              [Chart]                   | |
| |                              |   |                                        | |
| +------------------------------+   +----------------------------------------+ |
|                                                                                |
| ONBOARDING FUNNEL                 PLATFORM HEALTH                              |
| +------------------------------+  +-----------------------------------------+|
| | Submitted                    |  | Authentication: Operational             ||
| | Approved                     |  | Appointment API: Operational            ||
| | Completed                    |  | Queue API: Operational                  ||
| +------------------------------+  +-----------------------------------------+|
|                                                                                |
| [View Organizations] [View Subscriptions] [View Onboarding]                   |
+--------------------------------------------------------------------------------+
```

## 8.2 Organization Admin Analytics

```text
+--------------------------------------------------------------------------------+
| ORGANIZATION ANALYTICS                 [Date Range v] [All Branches v] [Export]|
+--------------------------------------------------------------------------------+
| APPOINTMENTS | COMPLETED | CANCELLED | NO-SHOW | WALK-INS                      |
|     850      |    690    |    55     |   30    |    75                         |
+--------------------------------------------------------------------------------+
| APPOINTMENT TREND                  APPOINTMENT OUTCOMES                         |
| +------------------------------+   +----------------------------------------+ |
| |                              |   | Completed / Cancelled / No-show         | |
| |        [Line Chart]          |   |                [Chart]                  | |
| |                              |   |                                        | |
| +------------------------------+   +----------------------------------------+ |
|                                                                                |
| BRANCH COMPARISON                  QUEUE PERFORMANCE                           |
| +------------------------------+  +-----------------------------------------+|
| | Main       420               |  | Average waiting: 24 min                 ||
| | North      260               |  | Maximum waiting: 68 min                 ||
| | South      170               |  | Average queue: 11                      ||
| +------------------------------+  +-----------------------------------------+|
|                                                                                |
| [Appointments] [Queue] [Doctors] [Rooms] [Branches] [Patient Activity]         |
+--------------------------------------------------------------------------------+
```

## 8.3 Appointment Analytics

```text
+--------------------------------------------------------------------------------+
| APPOINTMENT ANALYTICS                                                          |
+--------------------------------------------------------------------------------+
| Date [Last 30 Days v] Branch [All v] Doctor [All v] Source [All v]             |
| Status [All v] Model [All v]                                 [Apply Filters]   |
+--------------------------------------------------------------------------------+
| CREATED | COMPLETED | CANCELLED | NO-SHOW | RESCHEDULED                         |
|   850   |    690    |    55     |   30    |    75                              |
+--------------------------------------------------------------------------------+
| DAILY APPOINTMENT VOLUME                                                       |
| +----------------------------------------------------------------------------+ |
| |                            [Line Chart]                                   | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| APPOINTMENT OUTCOMES                                                          |
| +----------------------------------------------------------------------------+ |
| | Date | Created | Completed | Cancelled | No-show | Rescheduled              | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [Export CSV] [Export PDF]                                                     |
+--------------------------------------------------------------------------------+
```

## 8.4 Queue Analytics

```text
+--------------------------------------------------------------------------------+
| QUEUE ANALYTICS                                [Date Range v] [Branch v]       |
+--------------------------------------------------------------------------------+
| AVG WAIT | MAX WAIT | AVG QUEUE LENGTH | COMPLETION RATE | DELAYED             |
| 24 min   | 68 min   |       11         |      86%        |    14               |
+--------------------------------------------------------------------------------+
| WAITING TIME DISTRIBUTION             QUEUE ACTIVITY BY HOUR                   |
| +--------------------------------+    +------------------------------------+  |
| | 0-15 min       [Chart]         |    |                                    |  |
| | 15-30 min      [Chart]         |    |          [Chart]                   |  |
| | 30-60 min      [Chart]         |    |                                    |  |
| | Over 60 min    [Chart]         |    |                                    |  |
| +--------------------------------+    +------------------------------------+  |
|                                                                                |
| DOCTOR QUEUE SUMMARY                                                          |
| Doctor       | Avg Wait | Avg Queue | Completed | Delayed                      |
| Dr. Rahman   | 22 min   | 10        | 180       | 3                            |
| Dr. Karim    | 31 min   | 14        | 145       | 8                            |
+--------------------------------------------------------------------------------+
```

## 8.5 Doctor Analytics

```text
+--------------------------------------------------------------------------------+
| MY ANALYTICS — DR. RAHMAN                         [Last 30 Days v]              |
+--------------------------------------------------------------------------------+
| APPOINTMENTS | COMPLETED | AVG WAIT | SESSIONS | AVG DAILY APPOINTMENTS        |
|      420     |    350    | 22 min   |    24    |             14                |
+--------------------------------------------------------------------------------+
| APPOINTMENTS BY DAY                                                            |
| +----------------------------------------------------------------------------+ |
| |                            [Line Chart]                                   | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| SESSION SUMMARY                                                               |
| Active duration: 86 hours                                                     |
| Paused sessions: 2                                                            |
| Completed sessions: 24                                                       |
|                                                                                |
| QUEUE PERFORMANCE                                                             |
| Average waiting time: 22 minutes                                              |
| Queue completion rate: 90%                                                   |
+--------------------------------------------------------------------------------+
```

## 8.6 Assistant Analytics

```text
+--------------------------------------------------------------------------------+
| MY OPERATIONAL SUMMARY                            [Last 7 Days v]               |
+--------------------------------------------------------------------------------+
| QUEUE ACTIONS | PATIENTS CALLED | WALK-INS REGISTERED | REORDER ACTIONS         |
|      180      |      150        |        24           |       12               |
+--------------------------------------------------------------------------------+
| DAILY ACTIVITY                                                                |
| +----------------------------------------------------------------------------+ |
| |                            [Activity Chart]                               | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| ASSIGNED DOCTOR                                                               |
| Dr. Rahman                                                                    |
| Main Branch / Ground Floor / Room G-101                                      |
|                                                                                |
| [View Queue] [View Session Activity]                                          |
+--------------------------------------------------------------------------------+
```

## 8.7 Branch Analytics

```text
+--------------------------------------------------------------------------------+
| BRANCH ANALYTICS — MAIN BRANCH                 [Date Range v]                  |
+--------------------------------------------------------------------------------+
| APPOINTMENTS | COMPLETED | WALK-INS | AVG WAIT | ACTIVE ROOMS                  |
|     420      |    350    |    70    | 22 min   |       8                       |
+--------------------------------------------------------------------------------+
| HOURLY APPOINTMENT VOLUME             ROOM UTILIZATION                         |
| +--------------------------------+    +------------------------------------+  |
| |          [Chart]              |    |           [Heatmap]                 |  |
| +--------------------------------+    +------------------------------------+  |
|                                                                                |
| DOCTOR WORKLOAD                                                               |
| +----------------------------------------------------------------------------+ |
| | Doctor       | Appointments | Completed | Avg Wait | Sessions              | |
| +----------------------------------------------------------------------------+ |
|                                                                                |
| [Appointment Report] [Queue Report] [Room Report] [Walk-in Report]             |
+--------------------------------------------------------------------------------+
```

---

# 9. Report and Export Requirements

## 9.1 Supported reports

| Report ID | Report |
|---|---|
| REP-001 | Platform overview |
| REP-002 | Organization growth |
| REP-003 | Subscription status |
| REP-004 | Onboarding funnel |
| REP-005 | Appointment summary |
| REP-006 | Appointment outcomes |
| REP-007 | Walk-in activity |
| REP-008 | Queue waiting-time report |
| REP-009 | Queue movement report |
| REP-010 | Doctor operational summary |
| REP-011 | Branch comparison |
| REP-012 | Room utilization |
| REP-013 | Patient activity summary |
| REP-014 | Assistant operational activity |
| REP-015 | Session summary |

## 9.2 Export formats

Proposed formats:

- CSV for structured data.
- PDF for formatted reports.

Excel export may be introduced later if required.

## 9.3 Export controls

- Export permission must be separate from view permission.
- Every export must enforce the same filters and authorization as the screen.
- Patient-level fields must be omitted unless the role explicitly has permission.
- Export records must include generation timestamp, timezone, filters and requesting actor.
- Export actions should be auditable.
- Public display interfaces must not provide report exports.

---

# 10. Analytics Data Model Requirements

The following is a logical model. It does not prescribe the final physical database design.

| Entity | Important fields |
|---|---|
| AnalyticsEvent | event_id, type, occurred_at, organization_id, branch_id, actor_id, subject_id |
| AppointmentEvent | appointment_id, status, source, event_time, actor_id |
| QueueEvent | queue_entry_id, appointment_id, event_type, position, event_time |
| QueueSnapshot | queue_id, waiting_count, snapshot_time |
| DoctorSessionEvent | session_id, doctor_id, event_type, event_time |
| RoomAssignmentEvent | room_id, doctor_id, session_id, event_type, event_time |
| OrganizationEvent | organization_id, event_type, event_time |
| SubscriptionEvent | subscription_id, plan_id, status, event_time |
| StaffActivityEvent | actor_id, action, branch_id, subject_id, event_time |

### 10.1 Important relationship requirements

- Every appointment belongs to one organization and branch.
- Appointment records retain their original branch when transferred.
- Rescheduled appointments retain a link to the original appointment.
- Queue entries must have distinct queue-instance identifiers.
- Doctor sessions must identify the assigned doctor and branch.
- Room assignments must retain their effective period and history.
- Assistant activity must identify the authenticated assistant.
- Historical events must not be rewritten when the current record changes.

### 10.2 Aggregation strategy

Recommended initial approach:

1. Persist operational events reliably.
2. Generate daily and hourly aggregate tables or materialized views.
3. Reconcile aggregate values against source records.
4. Refresh affected aggregates when new events arrive.
5. Support direct source-event inspection for authorized audit purposes.

Do not introduce a complex streaming analytics platform before the operational data model is stable.

---

# 11. Accuracy, Edge Cases and Reconciliation

## 11.1 Duplicate events

Consumers must detect duplicate event IDs and avoid double-counting.

## 11.2 Rescheduled appointments

A rescheduled appointment must not be counted as two completed visits.

The original and replacement records must be reported separately for booking activity and linked for outcome analysis.

## 11.3 Branch transfers

Report appointment creation at the original branch and operational activity at the branch where the appointment was actually served. Do not silently overwrite the original branch.

## 11.4 Late arrivals

Late arrival is an operational indicator, not a no-show.

A late patient must not be automatically counted as absent.

## 11.5 No-shows

Only count a no-show after an authorized staff member confirms the state.

## 11.6 Open sessions

Open sessions must not be counted as completed sessions.

Their duration can be reported as elapsed duration only when clearly labelled as ongoing.

## 11.7 Paused sessions

Paused intervals must be excluded from active session duration.

## 11.8 Missing timestamps

If required timestamps are missing or invalid, exclude the record from duration calculations and display a data-quality warning.

## 11.9 Zero denominators

When the denominator is zero, display N/A rather than 0%.

## 11.10 Data reconciliation

The analytics service must support checks such as:

- Completed appointment totals versus appointment records.
- Queue completion totals versus queue entries.
- Session durations versus session event intervals.
- Subscription counts versus current subscription records.

---

# 12. Security and Privacy

1. Enforce tenant isolation at the API and database access layers.
2. Do not rely on frontend hiding to protect reports.
3. Do not expose patient names or mobile numbers in platform analytics.
4. Do not expose one organization's records to another organization.
5. Enforce branch scope for branch roles.
6. Restrict doctors to their own authorized operational records.
7. Restrict assistants to assigned operational scope.
8. Log analytics exports.
9. Protect aggregate queries against unauthorized drill-down into patient identities.
10. Apply appropriate retention and backup controls to event data.
11. Do not allow users to modify historical analytics events.
12. Ensure all report APIs use the authenticated actor's permissions.

---

# 13. Non-Functional Requirements

| Requirement | Target / rule |
|---|---|
| Tenant isolation | Mandatory |
| Authorization | Server-side, every request |
| Data freshness | Dashboard should show last-updated timestamp |
| Dashboard response | Target under 3 seconds for common cached reports |
| Detailed report response | Target under 5 seconds for normal reporting periods |
| Event idempotency | Mandatory |
| Timezone handling | Organization timezone |
| Export audit | Mandatory |
| Responsive design | Desktop, tablet and mobile |
| Localization | Bangla and English |
| Low bandwidth | Paginated tables and efficient chart payloads |
| Accessibility | Keyboard-accessible filters and readable charts |
| Empty states | Required |
| Error states | Required |
| Data-quality indicators | Required for incomplete metrics |

Performance targets are proposed engineering targets, not verified current system capabilities.

---

# 14. Implementation Phases

## P0 — MVP Analytics

- Organization appointment summary.
- Completed, cancelled and no-show counts.
- Scheduled versus walk-in counts.
- Queue average waiting time.
- Queue completion rate.
- Doctor operational summary.
- Branch-level appointment and queue reports.
- Platform organization and subscription overview.
- Role-scoped analytics permissions.
- Event capture and reconciliation.

## P1 — Expanded Analytics

- Branch comparison.
- Room utilization.
- Session analytics.
- Hourly queue patterns.
- Patient activity summary.
- Assistant activity summary.
- Onboarding funnel.
- Subscription usage trends.
- CSV/PDF export.
- Analytics data-quality monitoring.

## P2 — Advanced Analytics

- Configurable report builder.
- Custom dashboards.
- More detailed operational trend analysis.
- Scheduled report delivery.
- Additional historical comparisons.

P2 features must not delay the core operational MVP.

---

# 15. Acceptance Criteria

The Analytics module is ready for MVP acceptance only when:

1. A user cannot access analytics outside their authorized organization or branch.
2. A doctor cannot access another doctor's personal analytics without explicit authorization.
3. An assistant cannot access unrelated doctors or branches.
4. Platform analytics contains no patient-level identifying information.
5. Appointment counts reconcile with source records.
6. Completed, cancelled, no-show and rescheduled appointments are counted according to the approved definitions.
7. Waiting time is measured from queue entry to consultation start.
8. Queue length is calculated using documented snapshots.
9. Room utilization uses configured availability and session events.
10. Session pause periods are excluded from active duration.
11. Duplicate events do not inflate counts.
12. Missing timestamps do not create fabricated durations.
13. Zero denominators produce N/A.
14. Filters are consistently applied to metrics, charts and exports.
15. Exports are permission-controlled and auditable.
16. Bangla and English interfaces display dates, numbers and labels correctly.
17. Dashboard data freshness is visible.
18. All important metrics have automated tests.

---

# 16. Open Product Decisions

The following require explicit product-owner approval before implementation:

1. Should Platform Admin see only aggregate organization metrics, or also detailed organization usage records that contain no patient data?
2. Should receptionists have access to branch analytics by default, or only appointment and queue summaries?
3. Should doctors be allowed to view their own historical patient appointment activity in analytics?
4. Should room utilization be based on scheduled availability, actual active session time, or both as separate metrics?
5. Should queue snapshots be captured at a fixed interval (for example, every five minutes) or at each queue-changing event plus periodic sampling?
6. Should operational reports support CSV only in MVP, with PDF in P1?
7. What retention period should apply to detailed analytics events and aggregated historical data?

Until these decisions are approved, use the proposed defaults and keep the relevant permissions/configurations explicit.

---

# 17. Final Product Rule

AMSDP Analytics is an operational intelligence module.

It reports what happened in the appointment, queue, session, room, organization and subscription workflows.

It does not evaluate medical treatment, diagnose patients, measure clinical outcomes, manage finances or replace a hospital's clinical information system.

**End of AMSDP Analytics Specification V1.0**

There should be three administration levels:
- Platform Super Admin: defines global options, permitted ranges and defaults.
- Organization Admin: configures analytics preferences within platform limits.
- Branch Admin: configures branch-level options where the organization permits overrides.
1. New UI — Analytics Configuration
Add these navigation items:
ADMINISTRATION
|
+-- Analytics & Reports
|   +-- Overview
|   +-- Appointment Analytics
|   +-- Queue Analytics
|   +-- Doctor Analytics
|   +-- Room Analytics
|   +-- Branch Comparison
|
+-- Analytics Configuration
    +-- Visibility & Permissions
    +-- Metric Configuration
    +-- Queue Measurement
    +-- Room Utilization
    +-- Data Retention
    +-- Export Settings
    +-- Configuration History

2. Seven configurable decisions
Decision	Configuration	Default
1. Platform analytics visibility	Aggregate-only or detailed non-patient usage	Aggregate-only
2. Receptionist analytics access	No access, summary, or full authorized branch analytics	Summary
3. Doctor historical patient activity	Enable/disable own historical appointment activity	Enabled, authorized scope
4. Room utilization calculation	Scheduled availability, active session time, or both	Both, separately reported
5. Queue snapshot frequency	Event-driven and periodic sampling interval	5 minutes
6. Export formats	CSV, PDF, Excel; configure by role	CSV
7. Analytics event retention	Configurable retention periods for events and aggregates	Platform-defined policy


These are defaults, not hardcoded restrictions. Platform Admin can define which options are available to organizations.
3. Platform Admin — Global Analytics Configuration
+--------------------------------------------------------------------------------+
| PLATFORM ADMIN / ANALYTICS CONFIGURATION                                       |
+--------------------------------------------------------------------------------+
| GLOBAL DEFAULTS                                                                |
|                                                                                |
| 1. PLATFORM ANALYTICS VISIBILITY                                               |
|    (o) Aggregate-only                                                         |
|    ( ) Detailed organization usage (no patient identity)                     |
|                                                                                |
| 2. RECEPTIONIST ANALYTICS ACCESS                                               |
|    [x] No access                                                              |
|    [x] Summary access                                                         |
|    [x] Full authorized branch access                                          |
|    Default: [Summary v]                                                       |
|                                                                                |
| 3. DOCTOR HISTORICAL PATIENT ACTIVITY                                          |
|    [x] Allow                                                                 |
|    [ ] Deny                                                                   |
|    Default: [Enabled v]                                                       |
|                                                                                |
| 4. ROOM UTILIZATION                                                           |
|    [x] Scheduled availability                                                |
|    [x] Actual active session time                                             |
|    Default: [Both v]                                                          |
|                                                                                |
| 5. QUEUE SNAPSHOT FREQUENCY                                                    |
|    Event-driven: [Enabled v]                                                  |
|    Periodic interval: [5] minutes                                             |
|    Minimum interval: [1] minute                                                |
|                                                                                |
| 6. EXPORT FORMATS                                                             |
|    [x] CSV     [ ] PDF     [ ] Excel                                           |
|    Default: CSV                                                               |
|                                                                                |
| 7. DATA RETENTION                                                             |
|    Detailed events: [365] days                                                |
|    Aggregated data:  [1095] days                                               |
|                                                                                |
| [Discard Changes]                                  [Save Global Defaults]     |
+--------------------------------------------------------------------------------+

The checkboxes above represent platform-allowed options. The administrator selects which options organizations may configure.
4. Organization Admin — Analytics Settings
+--------------------------------------------------------------------------------+
| ORGANIZATION ADMIN / ANALYTICS SETTINGS                                        |
+--------------------------------------------------------------------------------+
| Organization: City Hospital                                                   |
|                                                                                |
| PLATFORM POLICY                                                                |
| Platform analytics visibility: Aggregate-only                                 |
| Receptionist analytics: Summary / Full branch (allowed)                       |
| Doctor historical activity: Allowed                                           |
| Room utilization: Both methods allowed                                       |
| Queue snapshot interval: 1–15 minutes                                         |
| Export formats: CSV, PDF                                                      |
| Detailed event retention: 365 days                                            |
|                                                                                |
| ORGANIZATION PREFERENCES                                                       |
| Receptionist access: [Summary v]                                               |
| Doctor historical activity: [Enabled v]                                       |
| Room utilization: [Both v]                                                     |
| Queue snapshot interval: [5] minutes                                           |
| Export formats: [x] CSV  [x] PDF                                              |
|                                                                                |
| [Reset to Platform Defaults]                     [Save Organization Settings] |
+--------------------------------------------------------------------------------+

The organization cannot select an option outside the platform's allowed configuration.
5. Branch Admin — Branch-Level Overrides
+--------------------------------------------------------------------------------+
| BRANCH ADMIN / ANALYTICS SETTINGS                                              |
+--------------------------------------------------------------------------------+
| Branch: Main Branch                                                           |
|                                                                                |
| Organization Policy:                                                          |
| Queue Snapshot Interval: 5 minutes                                            |
| Room Utilization: Both                                                        |
|                                                                                |
| BRANCH OVERRIDES                                                               |
| [ ] Use custom queue snapshot interval                                         |
|     Custom interval: [____] minutes                                            |
|                                                                                |
| [ ] Use custom room utilization method                                         |
|     Method: [Both v]                                                          |
|                                                                                |
| [ ] Override receptionist analytics access                                    |
|     Access: [Summary v]                                                       |
|                                                                                |
| [Save Branch Settings]                                                        |
+--------------------------------------------------------------------------------+

Branch overrides should only be available when the organization administrator explicitly enables them.
6. Configuration inheritance
Use this hierarchy:
PLATFORM SUPER ADMIN
        |
        | Defines allowed options, limits and defaults
        v
ORGANIZATION ADMIN
        |
        | Selects organization preferences
        v
BRANCH ADMIN
        |
        | Optional permitted branch overrides
        v
ANALYTICS ENGINE
        |
        v
ROLE-BASED ANALYTICS UI

Rules:
1. Platform restrictions always take precedence.
2. Organization settings inherit platform defaults.
3. Branch settings inherit organization settings.
4. An override is effective only when explicitly permitted.
5. Existing historical reports retain their original source data and metric definitions.
6. Configuration changes must be audited.
7. Invalid configurations must fail validation rather than silently fall back.
7. Configuration data model
Add these logical entities:
Entity	Purpose
AnalyticsConfigDefinition	Defines available settings and their validation rules
PlatformAnalyticsConfig	Global options, limits and defaults
OrganizationAnalyticsConfig	Organization-specific preferences
BranchAnalyticsConfig	Optional branch overrides
AnalyticsConfigHistory	Records configuration changes
AnalyticsConfigPermission	Controls which roles can change each setting


Every configuration record should include:
- Configuration key.
- Scope type.
- Scope ID.
- Current value.
- Previous value, where applicable.
- Updated by.
- Updated at.
- Version.
- Effective date.
- Reason for change, where required.
8. Important safeguards
Some settings are preferences, but others have security or data-integrity consequences.
- Platform visibility: organizations cannot expand Platform Admin access to patient-level information.
- Doctor historical activity: enabling this never bypasses patient-access permissions.
- Retention: an organization cannot extend or shorten retention beyond platform-defined legal and operational limits.
- Queue sampling: changing the interval must not rewrite historical measurements.
- Export formats: format access does not automatically grant data access.
- Metric formulas: administrators can select approved calculation methods, but cannot arbitrarily change metric definitions in a way that makes reports misleading.
9. Revised specification status
The seven previously open decisions are now converted into configurable requirements.

(Configuration approach established)

The Analytics Specification should be updated to V1.1 with these additions:
1. Analytics Configuration module.
2. Platform-level allowed options and defaults.
3. Organization-level preferences.
4. Optional branch overrides.
5. Configuration inheritance and validation.
6. Configuration audit history.
7. Settings-aware analytics API behavior.
One important distinction: configurable does not mean every role can change everything. Super Admin controls the policy; Organization Admin controls tenant preferences; Branch Admin receives only explicitly delegated overrides. This keeps AMSDP flexible without weakening tenant isolation or security.

AMSDP Analytics — Remaining ASCII UI Designs
1. Complete analytics navigation
The following is the consolidated navigation for the analytics module.
AMSDP
|
+-- ANALYTICS & REPORTS
|   |
|   +-- Overview
|   +-- Appointment Analytics
|   +-- Queue Analytics
|   +-- Doctor Analytics
|   +-- Branch Comparison
|   +-- Room Utilization
|   +-- Patient Activity
|   +-- Assistant Activity
|   +-- Operational Reports
|   |
|   +-- CONFIGURATION (Admin only)
|       |
|       +-- Analytics Overview
|       +-- Visibility & Permissions
|       +-- Metric Configuration
|       +-- Queue Measurement
|       +-- Room Utilization Settings
|       +-- Export Settings
|       +-- Data Retention
|       +-- Configuration History
|       +-- Data Quality & Reconciliation

Access to configuration screens depends on the administrator's role and permissions.
2. Analytics Configuration Overview
This is the landing page for administrators.
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION                              [Organization: City Hospital]
+--------------------------------------------------------------------------------+
| SETTINGS STATUS                                                                |
|                                                                                |
| VISIBILITY & ACCESS       METRIC SETTINGS       QUEUE MEASUREMENT              |
| Configured                Configured            Configured                     |
|                                                                                |
| ROOM UTILIZATION          EXPORT SETTINGS       DATA RETENTION                 |
| Configured                Configured            Configured                     |
+--------------------------------------------------------------------------------+
| CURRENT CONFIGURATION                                                          |
|                                                                                |
| Receptionist Access:       Summary                                               |
| Doctor Historical Data:    Enabled                                               |
| Room Utilization:          Both methods                                          |
| Queue Snapshot Interval:   5 minutes                                             |
| Export Formats:            CSV, PDF                                              |
| Event Retention:           365 days                                              |
| Aggregate Retention:       1095 days                                             |
+--------------------------------------------------------------------------------+
| CONFIGURATION INHERITANCE                                                      |
|                                                                                |
| Platform Defaults                                                              |
|       |                                                                        |
|       v                                                                        |
| Organization Preferences                                                      |
|       |                                                                        |
|       v                                                                        |
| Branch Overrides                                                               |
+--------------------------------------------------------------------------------+
| RECENT CONFIGURATION CHANGES                                                   |
|                                                                                |
| Setting                  Previous       Current        Updated By              |
| Queue Snapshot Interval  10 min         5 min           Org Admin              |
| Export Formats           CSV            CSV, PDF        Org Admin              |
|                                                                                |
| [View Configuration History]                                                  |
+--------------------------------------------------------------------------------+

3. Visibility and Permissions
This screen controls who can see which analytics.
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / VISIBILITY & PERMISSIONS                             |
+--------------------------------------------------------------------------------+
| Scope: [Organization v]                                                        |
| Branch: [All Branches v]                                                       |
+--------------------------------------------------------------------------------+
| ROLE PERMISSIONS                                                              |
|                                                                                |
| ANALYTICS MODULE          VIEW       EXPORT      CONFIGURE                     |
|--------------------------|-----------|-----------|-----------------------------|
| Super Admin              | Yes       | Yes       | Global                      |
| Organization Admin       | Yes       | Yes       | Organization               |
| Branch Admin             | Yes       | Yes       | Delegated settings          |
| Receptionist             | Summary   | No        | No                          |
| Doctor                   | Personal  | No        | No                          |
| Assistant                | Personal  | No        | No                          |
+--------------------------------------------------------------------------------+
| RECEPTIONIST ACCESS                                                            |
| Access Level: ( ) No Access                                                    |
|               (o) Summary Only                                                 |
|               ( ) Full Authorized Branch Analytics                            |
|                                                                                |
| DOCTOR HISTORICAL PATIENT ACTIVITY                                             |
| (o) Enabled     ( ) Disabled                                                   |
|                                                                                |
| ASSISTANT ANALYTICS                                                            |
| [x] Own activity                                                              |
| [x] Assigned doctor queue activity                                            |
| [ ] Other doctors' analytics                                                  |
|                                                                                |
| [ ] Allow branch-level override                                               |
|                                                                                |
| [Reset to Inherited Settings]                           [Save Changes]         |
+--------------------------------------------------------------------------------+

Important: a visibility setting does not override underlying patient-access permissions.
4. Metric Configuration
Administrators need a screen to manage approved metric definitions, thresholds and presentation.

Metric formulas should be governed centrally. They should not be freely editable text fields.
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / METRIC CONFIGURATION                                 |
+--------------------------------------------------------------------------------+
| Category: [All v] Status: [All v] Search [____________________] [Search]       |
+--------------------------------------------------------------------------------+
| METRIC ID | METRIC NAME         | FORMULA VERSION | STATUS   | ACTION           |
|-----------|---------------------|-----------------|----------|------------------|
| AP-011    | Completion Rate     | 1.0             | Active   | [View]           |
| QU-001    | Average Waiting     | 1.0             | Active   | [View]           |
| QU-004    | Queue Completion    | 1.0             | Active   | [View]           |
| DR-004    | Doctor Average Wait | 1.0             | Active   | [View]           |
| RM-004    | Room Utilization     | 1.0             | Active   | [View]           |
+--------------------------------------------------------------------------------+
| [View Metric Definitions]                                                     |
+--------------------------------------------------------------------------------+

Metric detail
+--------------------------------------------------------------------------------+
| METRIC DETAILS — QU-001                                                       |
+--------------------------------------------------------------------------------+
| Name: Average Waiting Time                                                     |
| Category: Queue Analytics                                                     |
| Version: 1.0                                                                  |
| Status: Active                                                                |
|                                                                                |
| DEFINITION                                                                     |
| Average time between queue entry and consultation start.                     |
|                                                                                |
| FORMULA                                                                        |
| Sum of valid waiting durations / Number of valid consultations started       |
|                                                                                |
| SOURCE EVENTS                                                                  |
| QueueEntered                                                                  |
| ConsultationStarted                                                           |
|                                                                                |
| EXCLUSIONS                                                                     |
| Cancelled before consultation                                                 |
| Invalid timestamp sequence                                                    |
| Appointments that never entered a queue                                       |
|                                                                                |
| UNIT: Minutes                                                                  |
|                                                                                |
| [View Change History]                         [Close]                         |
+--------------------------------------------------------------------------------+

Administrators may activate approved formula versions, but formula changes must go through controlled product/technical approval and versioning.
5. Queue Measurement Configuration
This screen implements the configurable snapshot frequency decision.
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / QUEUE MEASUREMENT                                    |
+--------------------------------------------------------------------------------+
| CONFIGURATION SCOPE                                                            |
| Scope: [Organization v]                                                        |
| Branch: [Main Branch v]                                                        |
+--------------------------------------------------------------------------------+
| QUEUE SNAPSHOT                                                                 |
|                                                                                |
| Event-driven snapshots:             [Enabled v]                                |
| Periodic snapshots:                 [Enabled v]                                |
| Periodic interval:                  [5] minutes                               |
|                                                                                |
| Allowed interval:                   1–15 minutes                               |
|                                                                                |
| [x] Capture when queue becomes active                                         |
| [x] Capture when queue becomes empty                                          |
| [x] Capture after queue reorder                                               |
| [x] Capture after patient call                                                |
|                                                                                |
| WAITING TIME THRESHOLDS                                                        |
| Normal wait:                        [15] minutes                               |
| Delayed wait:                       [30] minutes                               |
| Long wait:                           [60] minutes                              |
|                                                                                |
| [ ] Allow branch-specific settings                                            |
|                                                                                |
| [Reset to Platform Defaults]                           [Save Settings]         |
+--------------------------------------------------------------------------------+
| CURRENT EFFECTIVE SETTINGS                                                     |
| Snapshot interval: 5 minutes                                                   |
| Event-driven: Enabled                                                          |
| Source: Organization Configuration                                             |
+--------------------------------------------------------------------------------+

Thresholds determine how reports categorize waiting times. They must not change the underlying waiting-time formula.
6. Room Utilization Configuration
This screen supports both calculation methods.
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / ROOM UTILIZATION                                     |
+--------------------------------------------------------------------------------+
| SCOPE: [Organization v]                 BRANCH: [All Branches v]               |
+--------------------------------------------------------------------------------+
| ENABLED CALCULATION METHODS                                                    |
|                                                                                |
| [x] SCHEDULED AVAILABILITY UTILIZATION                                         |
|     Active assigned session time / Configured room availability               |
|                                                                                |
| [x] ACTUAL ACTIVE SESSION UTILIZATION                                         |
|     Actual active session time / Configured room availability                 |
|                                                                                |
| REPORT PRESENTATION                                                           |
| ( ) Scheduled utilization only                                                |
| ( ) Actual active utilization only                                             |
| (o) Show both separately                                                      |
|                                                                                |
| AVAILABILITY SOURCE                                                            |
| (o) Configured room availability schedule                                     |
| ( ) Organization-defined operating hours                                      |
|                                                                                |
| EXCLUSIONS                                                                     |
| [x] Exclude paused session intervals                                           |
| [x] Exclude cancelled sessions                                                 |
| [x] Exclude unavailable room periods                                           |
|                                                                                |
| [ ] Allow branch-specific overrides                                           |
|                                                                                |
| [Reset to Defaults]                                   [Save Settings]          |
+--------------------------------------------------------------------------------+

The formulas must be implemented carefully:
- Scheduled utilization = assigned scheduled session duration / available room duration.
- Actual utilization = actual active session duration / available room duration.
The denominator must use the same room and reporting period.
7. Export Settings
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / EXPORT SETTINGS                                     |
+--------------------------------------------------------------------------------+
| ALLOWED EXPORT FORMATS                                                         |
|                                                                                |
| [x] CSV                                                                       |
| [x] PDF                                                                       |
| [ ] Excel                                                                      |
|                                                                                |
| ROLE-BASED EXPORT PERMISSIONS                                                  |
|                                                                                |
| Role              CSV          PDF          Excel                              |
|-------------------|-------------|-------------|-------------------------------|
| Super Admin       [x]           [x]           [ ]                              |
| Organization Admin[x]           [x]           [ ]                              |
| Branch Admin      [x]           [x]           [ ]                              |
| Receptionist      [ ]           [ ]           [ ]                              |
| Doctor            [ ]           [ ]           [ ]                              |
| Assistant         [ ]           [ ]           [ ]                              |
+--------------------------------------------------------------------------------+
| EXPORT PRIVACY                                                                 |
| [x] Exclude patient mobile numbers by default                                 |
| [x] Include report filters in exported file                                   |
| [x] Include generated timestamp                                               |
| [x] Log every export                                                          |
|                                                                                |
| EXPORT LIMITS                                                                  |
| Maximum date range: [365] days                                                 |
| Maximum rows:        [100000]                                                  |
|                                                                                |
| [Save Export Settings]                                                        |
+--------------------------------------------------------------------------------+

A role's ability to export is separate from its ability to view analytics.

The export service must recheck authorization when generating the file.
8. Data Retention Configuration
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / DATA RETENTION                                       |
+--------------------------------------------------------------------------------+
| RETENTION POLICY                                                               |
|                                                                                |
| Detailed operational events                                                   |
| Retention: [365] days                                                          |
|                                                                                |
| Aggregated daily analytics                                                    |
| Retention: [1095] days                                                         |
|                                                                                |
| Aggregated monthly analytics                                                  |
| Retention: [Unlimited v]                                                      |
|                                                                                |
| CONFIGURATION SCOPE                                                            |
| (o) Organization policy                                                       |
| ( ) Branch-specific policy (if permitted)                                     |
|                                                                                |
| PLATFORM POLICY                                                                |
| Minimum permitted retention: [Platform-defined]                               |
| Maximum permitted retention: [Platform-defined]                               |
|                                                                                |
| DATA MANAGEMENT                                                                |
| [View Retention Status]                                                       |
| [View Scheduled Cleanup Jobs]                                                 |
|                                                                                |
| [Save Retention Policy]                                                       |
+--------------------------------------------------------------------------------+

Retention must be constrained by platform policy and applicable legal requirements. Organization Admin cannot reduce retention below the platform minimum.
9. Configuration History
Every configuration change needs an audit trail.
+--------------------------------------------------------------------------------+
| ANALYTICS CONFIGURATION / HISTORY                                              |
+--------------------------------------------------------------------------------+
| Date Range [Last 30 Days v] Actor [All v] Setting [All v] [Search]             |
+--------------------------------------------------------------------------------+
| Time       | Scope        | Setting          | Previous | New      | Actor     |
|------------|--------------|------------------|----------|----------|-----------|
| 11:20      | Organization | Queue Interval   | 10 min   | 5 min    | Org Admin |
| 10:55      | Organization | Export Format    | CSV      | CSV, PDF | Org Admin |
| 09:40      | Platform     | Doctor History   | Disabled | Enabled  | Super Admin|
+--------------------------------------------------------------------------------+
| SELECTED CHANGE                                                                |
| Setting: Queue Snapshot Interval                                              |
| Scope: Main Branch                                                            |
| Previous Value: 10 minutes                                                    |
| New Value: 5 minutes                                                          |
| Changed By: Organization Admin                                                |
| Reason: Improve queue reporting accuracy                                      |
| Effective From: 06 Nov 2026 11:20                                             |
|                                                                                |
| [View Related Audit Record]                                                   |
+--------------------------------------------------------------------------------+

No user should be able to edit or delete configuration history.
10. Data Quality and Reconciliation
This screen helps administrators understand whether analytics can be trusted.
+--------------------------------------------------------------------------------+
| ANALYTICS / DATA QUALITY                                                       |
+--------------------------------------------------------------------------------+
| SCOPE: [Organization v]     DATE: [Last 7 Days v]                              |
+--------------------------------------------------------------------------------+
| DATA QUALITY SUMMARY                                                           |
|                                                                                |
| VALID EVENTS       INVALID EVENTS      DUPLICATE EVENTS      MISSING TIMESTAMPS|
|    12,450                12                   4                    8           |
+--------------------------------------------------------------------------------+
| RECONCILIATION CHECKS                                                          |
|                                                                                |
| Appointment totals         [PASS]                                              |
| Queue completion totals    [PASS]                                              |
| Session duration totals    [WARNING]                                           |
| Room utilization totals    [PASS]                                              |
| Subscription counts        [PASS]                                              |
+--------------------------------------------------------------------------------+
| WARNINGS                                                                       |
|                                                                                |
| 8 queue events have missing consultation timestamps.                          |
| 2 sessions have an unmatched pause event.                                     |
| 4 duplicate events were ignored.                                               |
|                                                                                |
| [View Affected Records] [Export Data Quality Report]                          |
+--------------------------------------------------------------------------------+

This screen should be accessible to appropriately authorized administrators and technical support roles, not ordinary staff.
11. Common Analytics UI States
These states are essential across all dashboards, charts and reports.
11.1 Loading
+--------------------------------------------------------------------------------+
| APPOINTMENT ANALYTICS                                                          |
+--------------------------------------------------------------------------------+
| Date: Last 30 Days                                                             |
|                                                                                |
| [Loading metric cards...]                                                      |
|                                                                                |
| [Loading chart...]                                                             |
|                                                                                |
| [Loading report table...]                                                      |
+--------------------------------------------------------------------------------+

11.2 No data
+--------------------------------------------------------------------------------+
| QUEUE ANALYTICS                                                                |
+--------------------------------------------------------------------------------+
|                                                                                |
|                              No Data Available                                |
|                                                                                |
|                 There are no queue records for this period.                   |
|                                                                                |
|                 Try a different date range or branch.                         |
|                                                                                |
|                              [Change Filters]                                 |
+--------------------------------------------------------------------------------+

11.3 Insufficient data
+--------------------------------------------------------------------------------+
| ROOM UTILIZATION                                                               |
+--------------------------------------------------------------------------------+
|                                                                                |
|                         Insufficient Data                                     |
|                                                                                |
|           Room availability has not been configured for this period.          |
|                                                                                |
|           Utilization cannot be calculated reliably.                          |
|                                                                                |
|                         [Review Room Settings]                                |
+--------------------------------------------------------------------------------+

11.4 Permission denied
+--------------------------------------------------------------------------------+
| ACCESS RESTRICTED                                                              |
+--------------------------------------------------------------------------------+
|                                                                                |
|                         You do not have permission                            |
|                         to view this analytics report.                        |
|                                                                                |
|                         Contact your administrator.                           |
|                                                                                |
|                         [Back to Dashboard]                                   |
+--------------------------------------------------------------------------------+

11.5 Data freshness warning
+--------------------------------------------------------------------------------+
| ORGANIZATION ANALYTICS                                                        |
+--------------------------------------------------------------------------------+
| [!] Analytics data may be delayed.                                             |
|                                                                                |
| Last successful update: 11:20 AM                                              |
| Current time: 11:32 AM                                                        |
|                                                                                |
| Some recent queue events may not yet appear in this report.                    |
+--------------------------------------------------------------------------------+

12. Updated Screen Inventory
The following inventory consolidates the analytics designs.
ID	Screen	Role	Priority
AN-001	Platform Analytics Overview	Super Admin	P0
AN-002	Organization Analytics Overview	Org Admin	P0
AN-003	Branch Analytics Overview	Branch Admin	P0
AN-004	Appointment Analytics	Authorized roles	P0
AN-005	Queue Analytics	Authorized roles	P0
AN-006	Doctor Analytics	Admin / Doctor	P0
AN-007	Assistant Activity Analytics	Admin / Assistant	P1
AN-008	Branch Comparison	Org Admin	P1
AN-009	Room Utilization	Org / Branch Admin	P1
AN-010	Patient Activity	Org Admin	P1
AN-011	Operational Reports	Authorized roles	P1
AN-012	Analytics Configuration Overview	Admin	P0
AN-013	Visibility & Permissions	Admin	P0
AN-014	Metric Configuration	Super Admin / authorized admin	P1
AN-015	Queue Measurement	Admin	P0
AN-016	Room Utilization Settings	Admin	P1
AN-017	Export Settings	Admin	P1
AN-018	Data Retention	Super Admin / Org Admin within limits	P1
AN-019	Configuration History	Admin	P0
AN-020	Data Quality & Reconciliation	Admin / authorized support	P1
AN-021	Loading / Empty / Error States	All authorized roles	P0


13. Final navigation integration
The completed analytics module now fits into the full AMSDP architecture:
AMSDP
|
+-- PLATFORM ADMIN
|   +-- Dashboard
|   +-- Organizations
|   +-- Onboarding
|   +-- Subscription Plans
|   +-- Subscriptions
|   +-- Platform Users
|   +-- Analytics & Reports
|   +-- Analytics Configuration
|   +-- System Monitoring
|   +-- Audit & Security
|
+-- ORGANIZATION ADMIN
|   +-- Dashboard
|   +-- Branches
|   +-- Staff & Permissions
|   +-- Doctors
|   +-- Patients
|   +-- Floors & Rooms
|   +-- Analytics & Reports
|   +-- Analytics Configuration
|   +-- Organization Settings
|
+-- BRANCH ADMIN
|   +-- Dashboard
|   +-- Appointments
|   +-- Queue
|   +-- Doctors & Schedules
|   +-- Rooms & Sessions
|   +-- Analytics & Reports
|   +-- Branch Analytics Settings (delegated)
|
+-- RECEPTIONIST
|   +-- Dashboard
|   +-- Patient Registration
|   +-- Appointments
|   +-- Walk-ins
|   +-- Queue
|   +-- Authorized Operational Reports
|
+-- DOCTOR
|   +-- Dashboard
|   +-- My Appointments
|   +-- My Queue
|   +-- My Schedule
|   +-- My Rooms & Sessions
|   +-- My Analytics
|
+-- ASSISTANT
    +-- Dashboard
    +-- Assigned Doctor
    +-- Chamber / Room
    +-- Doctor Queue
    +-- Today's Appointments
    +-- Walk-in Registration (permission-based)
    +-- My Operational Summary

14. Final assessment
(ASCII analytics UI coverage completed)

The analytics design now covers:
- All five analytics access levels.
- All seven configurable decisions.
- Platform, organization and branch configuration.
- Metric governance.
- Queue and room measurement settings.
- Export and retention settings.
- Configuration audit history.
- Data quality and reconciliation.
- Loading, empty, error and permission states.
