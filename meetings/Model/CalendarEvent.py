"""
A class for time chunk on google calendar
Credits: agenda.py from Professor Young
"""
import datetime

BUSY = "BUSY"
FREE = "FREE"


class CalendarEvent(object):
    def __init__(self, start_time, end_time, date, summary=None, description=None, id=None, status=BUSY):
        """
        Initialization method for CalendarEvent
        Args:
            start_time: a time without date, start time of one event
            end_time: a time without date, end time of one event
                Example for time: "14:30:00-08:00"
            date: a date of a even
                Example for date: "2014-01-01"
            summary: a list, the summary of the event
            status: a string, shows 'busy' or 'free'
            description: a string, the content of the event
        Note: I use s_time and e_time to represent the time in one day. 
              If the start/end time is like above, the s/e time will be 14:30:00-08:00
              I use it to compute one day's event
        """
        self.start = start_time
        self.end = end_time
        self.date = date
        self.summary = summary
        self.description = description
        self.id = id
        self.status = status

    def get_start_time(self):
        """
        get the start time to sort
        """
        return self.assemble_time(self.start)

    def get_end_time(self):
        """
        get the end time to sort
        """
        return self.assemble_time(self.end)

    def get_date(self):
        """
        get the end time to sort
        """
        return self.date

    def get_id(self):
        """
        get the id
        """
        return self.id

    def assemble_time(self, time):
        """
        translate time to be ISO formate
        """
        iso_time = self.date + "T" + time
        return iso_time

    def __lt__(self, other):
        """
        compare time.
        Return:
            True if and only if the other is done by the time this event begins
        """
        return self.end <= other.start

    def __gt__(self, other):
        """
        compare time.
        Return:
            True if and only if the other is done before the time this event begins
        """
        return self.end > other.start

    def overlap(self, other):
        """
        check whether events are overlap
        """
        return not (self < other or other < self)

    # def translator_classToDict(self):
    #     """
    #     translate event class object to a list of dictionaries
    #     Args:
    #         self: a CalendarEvent object
    #     return;
    #         dictionary: a dictionaries, which is a event
    #     """
    #     event = {}
    #     event["id"] = self.id
    #     event["start_time"] = self.assemble_time(self.start)
    #     event["end_time"] = self.assemble_time(self.end)
    #     event["summary"] = self.summary
    #     event["description"] = self.description
    #     event["status"] = self.status
    #     return event

    def translator_toAppt(self):
        """
        translate Event to Appt
        I should re-write all but I don't have time. I have to make an interface
        """
        hours = self.start.split(":")[0]
        mins = self.start.split(":")[1]
        start = datetime.time(int(hours), int(mins))
        hours = self.end.split(":")[0]
        mins = self.end.split(":")[1]
        end = datetime.time(int(hours), int(mins))
        year, month, day = self.date.split("-")
        date = datetime.date(int(year), int(month), int(day))
        status = self.status
        return Appt(date, start, end, self.description, status)


    def union(self, other):
        """
        get the time union of two event if they are overlapped
        Args:
            other: another event object
        Return:
            return a new unioned event
        """
        new_start = min(self.start, other.start)
        new_end = max(self.end, other.end)
        return CalendarEvent(new_start, new_end, self.date)


# Class Agenda is from agenda.py whose author is Professor Young
# I tried to make my own agenda but it really takes time
# so I decieded to use professor's one but revised some codes to complete my project
# Link here: https://piazza.com/class_profile/get_resource/ihjisylll7y4az/ihjiszn8gh24ch from the prevsious piazza 322 "resource" section.
import datetime

class Appt:

    """
    A single appointment, starting on a particular
    date and time, and ending at a later time the same day.
    """
    
    def __init__(self, day, begin, end, desc, status=FREE):
        """Create an appointment on date
        from begin time to end time.
        
        Arguments:
            day:   A datetime.date object.  The appointment occurs this day.
            begin: A datetime.time object.  When the appointment starts. 
            end:  A datetime.time object, 
                after begin.                When the appointments ends.
            desc: A string describing the appointment
            
        Raises: 
        	ValueError if appointment ends before it begins
        	
        Example:
            Appt( datetime.date(2012,12,1),
                datetime.time(16,30),
                datetime.time(17,45))
            (December 1 from 4:30pm to 5:45pm)
        """
        self.begin = datetime.datetime.combine(day, begin)
        self.end = datetime.datetime.combine(day, end)
        self.status = status
        if begin >= end :
            raise ValueError("Appointment end must be after begin")
        self.desc = desc
        return

    @classmethod
    def from_string(cls, txt):
        """Factory parses a string to create an Appt"""
        fields = txt.split("|")
        if len(fields) != 2:
            raise ValueError("Appt literal requires exactly one '|' before description")
        timespec = fields[0].strip()
        desc = fields[1].strip()
        fields = timespec.split()
        if len(fields) != 3:
            raise ValueError("Appt literal must start with date, time, time, separated by blanks")
        appt_date_text = fields[0]
        appt_begin_text = fields[1]
        appt_end_text = fields[2]
        fields = appt_date_text.split(".")
        try:
            year = int(fields[0].strip())
            month = int(fields[1].strip())
            day = int(fields[2].strip())
        except:
            raise ValueError("Date in Appt literal should be 9999.99.99 (Year.Month.Day)")

        ### 
        date = datetime.date(year,month,day)
        begin = datetime.datetime.strptime(appt_begin_text, "%H:%M").time()
        end =   datetime.datetime.strptime(appt_end_text, "%H:%M").time()

        result = Appt(date, begin, end, desc)
        return result
       
    def get_begin(self):
        return self.begin

    def __lt__(self, other):
        """Does this appointment finish before other begins?
        
        Arguments:
        	other: another Appt
        Returns: 
        	True iff this Appt is done by the time other begins.
        """
        return self.end <= other.begin
        
    def __gt__(self, other):
        """Does other appointment finish before this begins?
        
        Arguments:
        	other: another Appt
        Returns: 
        	True iff other is done by the time this Appt begins
        """
        return other < self
    def translator_classToDict(self):
        """
        translate event class object to a list of dictionaries
        Args:
            self: a CalendarEvent object
        return;
            dictionary: a dictionaries, which is a event
        """
        event = {}
        event["start_time"] = self.begin.strftime("%Y-%m-%dT%H:%M") 
        event["end_time"] = self.end.strftime("%Y-%m-%dT%H:%M")
        event["description"] = self.desc
        event["status"] = self.status
        return event
    
    def get_date(self):

        return (self.begin.month, self.begin.day) 

    def overlaps(self, other):
        """Is there a non-zero overlap between this appointment
        and the other appointment?
		Arguments:
            other is an Appt
        Returns:
            True iff there exists some duration (greater than zero)
            between this Appt and other. 
        """
        return  not (self < other or other < self)
            
    def intersect(self, other, desc=""):
        """Return an appointment representing the period in
        common between this appointment and another.
        Requires self.overlaps(other).
        
		Arguments: 
			other:  Another Appt
			desc:  (optional) description text for this appointment. 

		Returns: 
			An appointment representing the time period in common
			between self and other.   Description of returned Appt 
			is copied from this (self), unless a non-null string is 
			provided as desc. 
        """
        if desc=="":
            desc = self.desc
        assert(self.overlaps(other))
        # We know the day must be the same. 
        # Find overlap of times: 
        #   Later of two begin times, earlier of two end times
        begin_time = max(self.begin.time(), other.begin.time())
        end_time = min(self.end.time(), other.end.time())
        return Appt(self.begin.date(), begin_time, end_time, desc)

    def union(self, other, desc=""):
        """Return an appointment representing the combined period in
        common between this appointment and another.
        Requires self.overlaps(other).
        
		Arguments: 
			other:  Another Appt
			desc:  (optional) description text for this appointment. 

		Returns: 
			An appointment representing the time period spanning
                        both self and other.   Description of returned Appt 
			is concatenation of two unless a non-null string is 
			provided as desc. 
        """
        if desc=="":
            desc = self.desc + " " + other.desc
        assert(self.overlaps(other))
        # We know the day must be the same. 
        # Find overlap of times: 
        #   Earlier of two begin times, later of two end times
        begin = min(self.begin, other.begin)
        end = max(self.end, other.end)
        return Appt(self.begin.date(), begin.time(), end.time(), desc)

class Agenda:
    """An Agenda is essentially a list of appointments,
    with some agenda-specific methods.
    """

    def __init__(self):
        """An empty agenda."""
        self.appts = [ ]
    
    def toList(self):
        return self.appts

    @classmethod
    def from_file(cls, f):
        """Factory: Read an agenda from a file.
        
        Arguments: 
            f:  A file object (as returned by io.open) or
               an object that emulates a file (like stringio). 
        returns: 
            An Agenda object
        """
        agenda = cls()
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                # Skip blank lines and comments
                pass
            else: 
                try: 
                    agenda.append(Appt.from_string(line))
                except ValueError as err: 
                    print("Failed on line: ", line)
                    print(err)
        return agenda

    def append(self,appt):
        """Add an Appt to the agenda."""
        self.appts.append(appt)

    def translator_classToDict():
        """
        translate it to dict
        """
        event = {}
        event["start_time"] = self.assemble_time(self.start)
        event["end_time"] = self.assemble_time(self.end)
        event["description"] = self.description
        event["status"] = FREE
        return event

    def intersect(self,other,desc=""): 
        """Return a new agenda containing appointments
        that are overlaps between appointments in this agenda
        and appointments in the other agenda.

        Titles of appointments in the resulting agenda are
        taken from this agenda, unless they are overridden with
        the "desc" argument.

        Arguments:
           other: Another Agenda, to be intersected with this one
           desc:  If provided, this string becomes the title of
                all the appointments in the result.
        """
        default_desc = (desc == "")
        result = Agenda()
        for thisappt in self.appts:
            if default_desc: 
                desc = thisappt.desc
            for otherappt in other.appts:
                if thisappt.overlaps(otherappt):
                    result.append(thisappt.intersect(otherappt,desc))
        
        return result

    def normalize(self):
        """Merge overlapping events in an agenda. For example, if 
        the first appointment is from 1pm to 3pm, and the second is
        from 2pm to 4pm, these two are merged into an appt from 
        1pm to 4pm, with a combination description.  
        After normalize, the agenda is in order by date and time, 
        with no overlapping appointments.
        """
        if len(self.appts) == 0:
            return

        ordering = lambda ap: ap.begin
        self.appts.sort(key=ordering)

        normalized = [ ]
        # print("Starting normalization")
        cur = self.appts[0]  
        for appt in self.appts[1:]:
            if appt > cur:
                # Not overlapping
                # print("Gap - emitting ", cur)
                normalized.append(cur)
                cur = appt
            else:
                # Overlapping
                # print("Merging ", cur, "\n"+
                #      "with    ", appt)
                cur = cur.union(appt)
                # print("New cur: ", cur)
        # print("Last appt: ", cur)
        normalized.append(cur)
        self.appts = normalized

    def normalized(self):
        """
        A non-destructive normalize
        (like "sorted(l)" vs "l.sort()").
        Returns a normalized copy of this agenda.
        """
        copy = Agenda()
        copy.appts = self.appts
        copy.normalize()
        return copy
        
    def complement(self, freeblock):
        """Produce the complement of an agenda
        within the span of a timeblock represented by 
        an appointment.  For example, 
        if this agenda is a set of appointments, produce a 
        new agenda of the times *not* in appointments in 
        a given time period.
        Args: 
           freeblock: Looking  for time blocks in this period 
               that are not conflicting with appointments in 
               this agenda.
        Returns: 
           A new agenda containing exactly the times that 
           are within the period of freeblock and 
           not within appointments in this agenda. The 
           description of the resulting appointments comes
           from freeblock.desc.
        """
        copy = self.normalized()
        comp = Agenda()
        day = freeblock.begin.date()
        desc = freeblock.desc
        cur_time = freeblock.begin
        for appt in copy.appts:
            if appt < freeblock:
                continue
            if appt > freeblock:
                if cur_time < freeblock.end:
                    comp.append(Appt(day,cur_time.time(),freeblock.end.time(), desc))
                    cur_time = freeblock.end
                break
            if cur_time < appt.begin:
                # print("Creating free time from", cur_time, "to", appt.begin)
                comp.append(Appt(day, cur_time.time(), appt.begin.time(), desc))
            cur_time = max(appt.end,cur_time)
        if cur_time < freeblock.end:
            # print("Creating final free time from", cur_time, "to", freeblock.end)
            comp.append(Appt(day, cur_time.time(), freeblock.end.time(), desc))
        return comp



    def __len__(self):
        """Number of appointments, callable as built-in len() function"""
        return len(self.appts)

    def __iter__(self):
        """An iterator through the appointments in this agenda."""
        return self.appts.__iter__()

    def __str__(self):
        """String representation of a whole agenda"""
        rep = ""
        for appt in self.appts:
            rep += str(appt) + "\n"
        return rep[:-1]

    def __eq__(self,other):
        """Equality, ignoring descriptions --- just equal blocks of time"""
        if len(self.appts) != len(other.appts):
            return False
        for i in range(len(self.appts)):
            mine = self.appts[i]
            theirs = other.appts[i]
            if not (mine.begin == theirs.begin and
                    mine.end == theirs.end):
                return False
        return True

    

if __name__ == "__main__":
    a = CalendarEvent("14:30:00-08:00", "14:30:00-08:00", "2014/01/01")
    b = CalendarEvent("11:30:00-08:00", "12:30:00-08:00", "2014/01/01")
    c = CalendarEvent("18:30:00-08:00", "20:30:00-08:00", "2014/01/01")
    d = CalendarEvent("21:30:00-08:00", "22:30:00-08:00", "2014/01/01")
    e = CalendarEvent("04:30:00-08:00", "23:30:00-08:00", "2014/01/01")