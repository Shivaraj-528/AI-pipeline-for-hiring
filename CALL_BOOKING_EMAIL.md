# Call Booking Email Feature

## 📧 Overview

When a candidate doesn't answer the phone call, the system automatically sends them a professional email with a link to book an interview at their convenience.

---

## 🎯 How It Works

### **Trigger Conditions**

The booking email is sent when:
1. ✅ Candidate passes resume screening
2. ✅ Candidate passes background verification
3. ❌ Phone call fails (no-answer, busy, failed, timeout)

### **Call Failure Scenarios**

| Scenario | VAPI Status | Action |
|----------|-------------|--------|
| No answer | `no-answer` | Send booking email |
| Line busy | `busy` | Send booking email |
| Call failed | `failed` | Send booking email |
| Call timeout | Timeout after 15 min | Send booking email |
| Call error | `error` | Send booking email |

---

## 📨 Email Content

### **Subject Line**
```
Interview Call - Schedule at Your Convenience | Arya Stack Technologies
```

### **Email Features**

✅ **Professional HTML Design**
- Company branding with green header
- Clear call-to-action button
- Responsive layout
- Plain text fallback

✅ **Key Information**
- Explanation of missed call
- Interview duration (15-20 minutes)
- Interview format (AI phone interview)
- Topics covered (MERN stack)
- Urgency (48-hour deadline)

✅ **Booking Link**
```
https://calendly.com/aryastack/interview
```

---

## 🔧 Implementation Details

### **Files Modified**

#### 1. `utils/email_service.py`
Added new function:
```python
send_call_booking_email(candidate_email, candidate_name="Candidate")
```

**Features:**
- HTML email with professional styling
- Plain text alternative
- Calendly integration
- Error handling
- Returns `True`/`False` for success/failure

#### 2. `main.py`
Enhanced call failure handling:
```python
if not interview_transcript:
    # Extract candidate name from resume
    # Send booking email
    # Exit gracefully
```

**Features:**
- Automatic name extraction from resume
- Fallback to "Candidate" if name not found
- Clear status messages
- Graceful exit

---

## 📋 Email Template

### **HTML Version**
- Green header with company name
- Centered booking button
- Bulleted list of interview details
- Professional footer
- Responsive design

### **Plain Text Version**
- Clean formatting
- All information included
- Works in any email client
- Accessible

---

## 🎨 Email Preview

```
┌─────────────────────────────────────────┐
│  Arya Stack Technologies                │
│  MERN Stack Developer - Interview       │
├─────────────────────────────────────────┤
│                                         │
│  Dear Arjun Kumar,                      │
│                                         │
│  Thank you for applying for the MERN    │
│  Stack Developer position!              │
│                                         │
│  We recently attempted to reach you     │
│  via phone but were unable to connect.  │
│                                         │
│  Good news! You can now schedule the    │
│  interview at a time that works best.   │
│                                         │
│     [📅 Book Your Interview Slot]       │
│                                         │
│  What to expect:                        │
│  • Duration: 15-20 minutes              │
│  • Format: Phone interview with AI      │
│  • Focus: MERN Stack questions          │
│  • Topics: MongoDB, Express, React, Node│
│                                         │
│  Important: Book within 48 hours        │
│                                         │
│  Best regards,                          │
│  HR Team                                │
│  Arya Stack Technologies                │
└─────────────────────────────────────────┘
```

---

## 🔄 Process Flow

```
Resume Screening ✅
       ↓
Background Verification ✅
       ↓
Interview Questions Generated ✅
       ↓
Phone Call Initiated 📞
       ↓
   [WAITING]
       ↓
   ┌─────────┐
   │ Answer? │
   └─────────┘
       ↓
    ┌──┴──┐
    │     │
   YES   NO
    │     │
    ↓     ↓
Interview  📧 Email Sent
Continues  "Book Your Slot"
    ↓         ↓
Evaluation  Process Paused
    ↓
Final Decision
```

---

## 🧪 Testing

### **Test Scenario 1: No Answer**
```bash
# Run the system
python3 main.py

# Don't answer the phone
# Expected: Booking email sent after timeout
```

### **Test Scenario 2: Busy Line**
```bash
# Run the system
python3 main.py

# Have another call active
# Expected: Booking email sent immediately
```

### **Verify Email Sent**
Check console output:
```
❌ Call failed with status: no-answer
📧 Sending call booking email to candidate...
✅ Call booking email sent to arjunkumar.dev@gmail.com
📅 Candidate can now schedule interview at their convenience
```

---

## 📝 Customization

### **Change Calendly Link**

Edit `utils/email_service.py` line ~105:
```python
<a href="https://calendly.com/YOUR_LINK/interview" class="button">
```

### **Change Deadline**

Edit `utils/email_service.py` line ~125:
```python
<p><strong>Important:</strong> Please book your slot within the next 48 hours
```

### **Change Email Styling**

Edit the CSS in `utils/email_service.py` lines ~70-85:
```python
.header {{ background-color: #4CAF50; ... }}  # Change color
.button {{ background-color: #4CAF50; ... }}  # Change button color
```

---

## 🔐 Requirements

### **Email Configuration**
Ensure `.env` has:
```
SENDER_EMAIL=your-email@gmail.com
SENDER_EMAIL_PASSWORD=your-app-password
```

### **Calendly Setup**
1. Create a Calendly account
2. Set up an event type for "Interview"
3. Update the link in `email_service.py`

---

## 📊 Success Metrics

The system will log:
- ✅ Email sent successfully
- ❌ Email failed to send
- 📧 Recipient email address
- 👤 Candidate name (if extracted)

---

## 🚀 Future Enhancements

Potential improvements:
1. **SMS Notification** - Send SMS in addition to email
2. **Multiple Attempts** - Retry call before sending email
3. **Custom Scheduling** - Generate unique Calendly links per candidate
4. **Email Tracking** - Track if candidate opened email
5. **Reminder Emails** - Send reminder after 24 hours if not booked
6. **WhatsApp Integration** - Send booking link via WhatsApp

---

## 💡 Best Practices

1. **Timing**: Send email immediately after call failure
2. **Urgency**: Include deadline to encourage quick booking
3. **Clarity**: Clearly explain what happened and next steps
4. **Professionalism**: Maintain professional tone
5. **Accessibility**: Provide both HTML and plain text versions

---

## 🐛 Troubleshooting

### Email not sending
**Check:**
- Gmail credentials in `.env`
- App password (not regular password)
- Internet connection
- SMTP not blocked by firewall

### Name extraction failing
**Solution:**
- System falls back to "Candidate"
- Manually update name in email template if needed

### Calendly link not working
**Check:**
- Link is publicly accessible
- Event type is active
- No typos in URL

---

## 📞 Support

For issues or questions:
- Check console logs for error messages
- Verify email credentials
- Test with a personal email first
- Review VAPI call logs for call failure reasons

---

## ✅ Summary

This feature ensures that **no qualified candidate is lost** due to missed phone calls. It provides a professional, automated way to reschedule interviews and maintain a positive candidate experience.

**Key Benefits:**
- 🎯 Better candidate experience
- 📈 Higher interview completion rate
- ⏰ Flexible scheduling
- 🤖 Fully automated
- 💼 Professional communication
