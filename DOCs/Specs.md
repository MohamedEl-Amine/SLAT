1.Face Recognition Attendance Terminal
2. Employee Profile – Face Definition (Enrollment)
2.1 Entry Point

In the Employee Profile screen, add an action button:

“Définir visage” (Define Face)

2.2 Behavior

When the user clicks “Définir visage”:

The system opens a live camera window.

The employee stands in front of the camera.

The system captures the employee’s face.

The system validates capture quality:

A face is detected.

Only one face is present.

The face is sufficiently frontal.

Image quality is sufficient for recognition.

The system generates and stores a biometric face profile for the employee.

If the employee already has a defined face:

The old face profile is replaced.

The operation is logged.

The system confirms successful face definition.

2.3 Rules

One active face profile per employee.

Only users with admin rights can define or redefine a face.

Face definition is mandatory for face-based attendance.

The system must not store raw face images permanently.

All face enrollment actions must be logged.

3. Public Terminal Page – Face Attendance
3.1 Entry Point

In the Terminal de Présence public screen:

The camera is always active or auto-activated when a person is in front of it.

3.2 Behavior

A person stands in front of the terminal camera.

The system detects a face.

The system validates detection:

One face only.

Sufficient quality.

The system attempts to identify the person using stored employee face profiles.

The system computes a confidence percentage (certainty level) for the best match.

The system displays:

The detected employee name (if matched).

The confidence percentage.

3.3 Decision Logic

If confidence ≥ acceptance threshold:

The employee is considered identified.

An attendance record is created.

A success message is displayed.

If confidence < acceptance threshold:

The employee is considered not recognized.

No attendance is created.

A failure message is displayed.

A fallback method is proposed (QR / Card / Manual).

4. Attendance Record

When face recognition succeeds, the system creates an attendance entry with:

Employee ID

Date and time

Attendance type (IN / OUT)

Method = FACE

Terminal ID

Confidence percentage

5. Security and Controls

Face enrollment requires admin privileges.

Face redefinition invalidates the previous biometric profile.

All enrollments and recognitions are logged.

The terminal must operate fully offline.

Only biometric profiles (not photos) are stored.

6. Non-Functional Constraints

The system must:

Work in real time.

Operate offline.

Be usable in a controlled indoor environment.

Provide deterministic results for the same input conditions.

7. Summary (What the dev must implement)

Employee Profile:

“Définir visage” button

Camera capture flow

Face validation

Biometric profile storage

Redefinition handling

Terminal de Présence:

Live camera

Face detection

Identification

Confidence percentage display

Threshold decision

Attendance creation

Fallback path