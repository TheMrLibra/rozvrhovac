import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type Language = 'en' | 'cs'

interface Translations {
  [key: string]: string | Translations
}

const translations: Record<Language, Translations> = {
  en: {
    common: {
      dashboard: 'Dashboard',
      logout: 'Logout',
      loading: 'Loading...',
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      close: 'Close',
      search: 'Search',
      filter: 'Filter',
      actions: 'Actions',
      name: 'Name',
      email: 'Email',
      role: 'Role',
      yes: 'Yes',
      no: 'No'
    },
    dashboard: {
      title: 'Dashboard',
      currentlyRunningLessons: 'Currently Running Lessons',
      noLessonsRunning: 'No lessons are currently running',
      break: 'Break',
      todaysAbsentTeachers: "Today's Absent Teachers",
      noTeachersAbsent: 'No teachers are absent today',
      class: 'Class',
      subject: 'Subject',
      teacher: 'Teacher',
      classroom: 'Classroom',
      timeRange: 'Time Range',
      reason: 'Reason'
    },
    navigation: {
      schoolSettings: 'School Settings',
      classes: 'Classes',
      teachers: 'Teachers',
      timetables: 'Timetables',
      teacherDashboard: 'Teacher Dashboard',
      reportAbsence: 'Report Absence',
      viewTimetable: 'View Timetable',
      scholarDashboard: 'Scholar Dashboard'
    },
    schoolSettings: {
      title: 'School Settings',
      back: 'Dashboard',
      configureSettings: 'Configure School Settings',
      configureDescription: 'Manage your school\'s timetable configuration including class hours, breaks, and lunch periods.',
      timeSettings: 'Time Settings',
      classHourSettings: 'Class Hour Settings',
      breakSettings: 'Break Settings',
      lunchSettings: 'Lunch Settings',
      startTime: 'Start Time',
      endTime: 'End Time',
      classHourLength: 'Class Hour Length (minutes)',
      breakDuration: 'Break Duration (minutes)',
      breakDurations: 'Break Durations (minutes)',
      defaultBreakDuration: 'Default Break Duration (minutes)',
      lunchDuration: 'Lunch Duration (minutes)',
      possibleLunchHours: 'Possible Lunch Hours',
      saveSettings: 'Save Settings',
      saving: 'Saving...',
      settingsSaved: 'Settings saved successfully',
      settingsError: 'Failed to save settings',
      schoolDayStart: 'School day start time',
      schoolDayEnd: 'School day end time',
      durationOfPeriod: 'Duration of each class period',
      breakAfterLesson: 'after lesson',
      addBreak: 'Add Break',
      removeBreak: 'Remove break',
      setBreakDurations: 'Set the duration for each break between lessons. The last break duration will be used for any additional breaks if needed.',
      fallbackDuration: 'Fallback duration if break_durations is not set',
      commaSeparatedHours: 'Comma-separated lesson indices when lunch is possible (e.g., 3,4,5). Lesson indices start from 1.'
    },
    classes: {
      title: 'Classes',
      back: 'Dashboard',
      selectClass: 'Select Class',
      selectAClass: 'Select a class...',
      timetable: 'Timetable',
      loadingTimetable: 'Loading timetable...',
      noTimetableAvailable: 'No timetable available for this class',
      subjects: 'Subjects',
      noSubjectsAllocated: 'No subjects allocated to this class',
      noPrimaryTeacher: 'No primary teacher',
      manageClass: 'Manage Class',
      manageSubjects: 'Manage Subjects',
      manageSubjectAllocations: 'Manage Subject Allocations for',
      addSubjectAllocation: 'Add Subject Allocation',
      selectSubject: 'Select Subject',
      weeklyHours: 'Weekly Hours',
      yearlyHours: 'Yearly Hours',
      hoursPerWeek: 'hours/week',
      hoursPerWeekPlaceholder: 'Hours per week',
      allowMultipleInOneDay: 'Allow multiple lessons per day',
      requiredConsecutiveHours: 'Required Consecutive Hours',
      requiredConsecutiveHoursPlaceholder: 'Number of lessons that must be in a row (optional)',
      teachers: 'Teachers',
      noTeachersAssigned: 'No teachers assigned',
      existingAllocations: 'Existing Allocations',
      currentSubjectAllocations: 'Current Subject Allocations',
      noAllocations: 'No allocations found',
      noSubjectAllocationsYet: 'No subject allocations yet',
      updateAllocation: 'Update',
      removeAllocation: 'Remove',
      addAllocation: 'Add Allocation',
      editSubjectAllocation: 'Edit Subject Allocation',
      selectPrimaryTeacher: 'Select Primary Teacher (optional)',
      primary: 'Primary',
      classInformation: 'Class Information',
      numberOfStudents: 'Number of Students',
      enterNumberOfStudents: 'Enter number of students',
      addClass: 'Add Class',
      editClass: 'Edit Class',
      deleteClass: 'Delete Class',
      className: 'Class Name',
      gradeLevel: 'Grade Level',
      noClasses: 'No classes found'
    },
    teachers: {
      title: 'Teachers',
      back: 'Dashboard',
      addNewTeacher: 'Add New Teacher',
      fullName: 'Full Name',
      maxWeeklyHours: 'Max Weekly Hours',
      availability: 'Availability',
      availabilityFormat: 'Format: day:hour1,hour2 (e.g., monday:1,2,3 tuesday:1,2)',
      availabilityPlaceholder: 'Availability (e.g., monday:1,2,3 tuesday:1,2)',
      addTeacher: 'Add Teacher',
      filterByTeacher: 'Filter by Teacher',
      allTeachers: 'All Teachers',
      todaysTimetableFor: "Today's Timetable for",
      loadingTimetable: 'Loading timetable...',
      noLessonsToday: 'No lessons scheduled for today',
      absencesFor: 'Absences for',
      loadingAbsences: 'Loading absences...',
      noAbsencesReported: 'No absences reported',
      reason: 'Reason',
      teachersList: 'Teachers List',
      maxHours: 'Max Hours',
      subjects: 'Subjects',
      noSubjectsAssigned: 'No subjects assigned',
      edit: 'Edit',
      manageSpecializations: 'Manage Specializations',
      reportAbsence: 'Report Absence',
      delete: 'Delete',
      subjectCapabilities: 'Subject Capabilities',
      addCapability: 'Add Capability',
      selectSubject: 'Select Subject',
      selectGradeLevel: 'Select Grade Level (optional)',
      selectClassGroup: 'Select Class Group (optional)',
      allClassesOrSelect: 'All Classes (or select specific class)',
      isPrimary: 'Is Primary Teacher',
      editTeacher: 'Edit Teacher',
      deleteTeacher: 'Delete Teacher',
      save: 'Save',
      cancel: 'Cancel',
      close: 'Close',
      noTeachers: 'No teachers found',
      seeAbsences: 'See Absences',
      capabilities: 'Capabilities',
      absences: 'Absences',
      reportAbsenceFor: 'Report Absence for',
      dateFrom: 'Date From',
      dateTo: 'Date To',
      reasonOptional: 'Reason (optional)',
      reasonForAbsence: 'Reason for absence',
      manageSpecializationsFor: 'Manage Specializations for',
      addNewSpecialization: 'Add New Specialization',
      addSpecialization: 'Add Specialization',
      currentSpecializations: 'Current Specializations',
      noSpecializationsYet: 'No specializations yet',
      class: 'Class',
      remove: 'Remove'
    },
    timetables: {
      title: 'Timetables',
      back: 'Dashboard',
      generateNewFixedTimetable: 'Generate New Fixed Timetable',
      generateTimetable: 'Generate Timetable',
      timetableName: 'Timetable Name',
      timetableNamePlaceholder: 'Timetable name (e.g., Spring 2025)',
      validFrom: 'Valid From',
      validTo: 'Valid To',
      generate: 'Generate',
      generating: 'Generating...',
      validating: 'Validating...',
      deleteTimetable: 'Delete Timetable',
      noTimetables: 'No timetables found',
      viewTimetable: 'View Timetable',
      view: 'View',
      validate: 'Validate',
      delete: 'Delete',
      calendar: 'Calendar',
      monthView: 'Month View',
      dayView: 'Day View',
      timetablesList: 'Timetables List',
      selectClass: 'Select Class',
      allClasses: 'All Classes',
      primary: 'Primary',
      substitute: 'Substitute',
      substituteForDate: 'Substitute for Date',
      isPrimary: 'Is Primary',
      entries: 'entries',
      actions: 'Actions',
      selectTimetable: 'Select Timetable',
      noTimetableSelected: 'No timetable selected',
      loadingTimetable: 'Loading timetable...',
      loadingTimetables: 'Loading timetables...',
      fixedTimetables: 'Fixed Timetables',
      substituteTimetables: 'Substitute Timetables',
      classTimetableCalendar: 'Class Timetable Calendar',
      valid: 'Valid',
      noValidityPeriodSet: 'No validity period set',
      noFixedTimetablesFound: 'No fixed timetables found. Generate one to get started.',
      noSubstituteTimetablesFound: 'No substitute timetables found.',
      generateSubstituteTimetable: 'Generate Substitute Timetable',
      selectBaseTimetable: 'Select Base Timetable',
      forDate: 'For Date',
      noDateSpecified: 'No date specified',
      generateSubstitute: 'Generate Substitute',
      notAvailable: 'N/A',
      timetableValid: 'Timetable is valid!',
      timetableValidationFailed: 'Timetable validation failed',
      validationError: 'Validation error',
      timetableGeneratedSuccessfully: 'Timetable generated successfully!',
      failedToGenerateTimetable: 'Failed to generate timetable',
      pleaseSelectBothDates: 'Please select both valid from and valid to dates',
      validFromMustBeBeforeValidTo: 'Valid from date must be before valid to date',
      confirmDeleteTimetable: 'Are you sure you want to delete this timetable?',
      monday: 'Monday',
      tuesday: 'Tuesday',
      wednesday: 'Wednesday',
      thursday: 'Thursday',
      friday: 'Friday',
      lunchBreak: 'Lunch Break'
    },
    documentation: {
      title: 'Documentation',
      back: 'Dashboard',
      admin: {
        title: 'Admin Features',
        schoolSettings: {
          title: 'School Settings',
          configureTimes: 'Configure school start and end times',
          configureClassHours: 'Set class hour length',
          configureBreaks: 'Configure break durations (variable breaks supported)',
          configureLunch: 'Set lunch duration and possible lunch hours'
        },
        classes: {
          title: 'Classes Management',
          viewTimetables: 'View timetables for each class',
          manageSubjects: 'Manage subject allocations for classes',
          assignPrimaryTeachers: 'Assign primary teachers for each subject per class',
          setStudentCount: 'Set number of students per class'
        },
        teachers: {
          title: 'Teachers Management',
          addEditTeachers: 'Add and edit teacher information',
          manageCapabilities: 'Manage teacher subject capabilities and class assignments',
          viewAbsences: 'View teacher absences and filter by date',
          viewTimetables: 'View daily timetables for teachers'
        },
        subjects: {
          title: 'Subjects Management',
          addEditSubjects: 'Add and edit subjects',
          configureConstraints: 'Configure subject constraints (consecutive hours, multiple per day, etc.)',
          manageAllocations: 'Manage class-subject allocations and weekly hours'
        },
        classrooms: {
          title: 'Classrooms Management',
          addEditClassrooms: 'Add and edit classroom information',
          setCapacity: 'Set maximum capacity for each classroom',
          assignSpecializations: 'Assign subject specializations to classrooms'
        },
        timetables: {
          title: 'Timetables Management',
          generateFixed: 'Generate fixed (primary) timetables for a specific period',
          generateSubstitute: 'Generate substitute timetables for days with teacher/classroom absences',
          validateTimetables: 'Validate timetables for conflicts and constraint violations',
          viewCalendar: 'View timetables in calendar format (month and day views)',
          deleteTimetables: 'Delete timetables (both fixed and substitute)'
        },
        dashboard: {
          title: 'Dashboard',
          viewRunningLessons: 'View currently running lessons across all classes',
          viewAbsentTeachers: 'View today\'s absent teachers'
        },
        howTo: {
          generateTimetable: {
            title: 'How to Generate a Fixed Timetable',
            step1: 'Navigate to the Timetables page from the dashboard',
            step2: 'Click "Generate New Fixed Timetable" button',
            step3: 'Enter a name for the timetable (e.g., "Spring 2025")',
            step4: 'Select the validity period (Valid From and Valid To dates)',
            step5: 'Click "Generate" and wait for the timetable to be created. It will be automatically validated after generation.'
          },
          assignPrimaryTeacher: {
            title: 'How to Assign a Primary Teacher to a Class Subject',
            step1: 'Navigate to the Classes page from the dashboard',
            step2: 'Select a class from the dropdown',
            step3: 'Click "Manage Subjects" button',
            step4: 'When adding or editing a subject allocation, select a primary teacher from the dropdown. The primary teacher will be used when generating fixed timetables.'
          },
          generateSubstitute: {
            title: 'How to Generate a Substitute Timetable',
            step1: 'Ensure you have at least one fixed (primary) timetable created',
            step2: 'Navigate to the Timetables page and scroll to "Generate Substitute Timetable" section',
            step3: 'Select the base timetable and choose the date for which you need a substitute',
            step4: 'Click "Generate Substitute". The system will create a new timetable accounting for teacher and classroom absences for that specific date.'
          }
        }
      },
      teacher: {
        title: 'Teacher Features',
        timetable: {
          title: 'Timetable',
          viewDailyTimetable: 'View your daily timetable with lesson times, subjects, classes, and classrooms',
          viewWeeklySchedule: 'View your weekly schedule'
        },
        absences: {
          title: 'Absences',
          reportAbsence: 'Report absences for specific dates and hours',
          viewAbsences: 'View your reported absences'
        },
        dashboard: {
          title: 'Dashboard',
          viewTodaysSchedule: 'View today\'s schedule and upcoming lessons',
          quickActions: 'Access quick actions and navigation'
        }
      }
    },
    subjects: {
      title: 'Subjects',
      back: 'Dashboard',
      addNewSubject: 'Add New Subject',
      subjectName: 'Subject Name',
      canBeMultipleTimesPerDay: 'Can be multiple times per day',
      mustBeConsecutive: 'Must be consecutive hours',
      consecutiveHours: 'Consecutive Hours',
      addSubject: 'Add Subject',
      subjectsList: 'Subjects List',
      editSubject: 'Edit Subject',
      deleteSubject: 'Delete Subject',
      save: 'Save',
      cancel: 'Cancel',
      noSubjects: 'No subjects found'
    },
    classrooms: {
      title: 'Classrooms',
      back: 'Dashboard',
      addNewClassroom: 'Add New Classroom',
      classroomName: 'Classroom Name',
      specializations: 'Specializations',
      selectSpecializations: 'Select Specializations (multiple)',
      noSpecialization: 'No specialization',
      addClassroom: 'Add Classroom',
      classroomsList: 'Classrooms List',
      editClassroom: 'Edit Classroom',
      deleteClassroom: 'Delete Classroom',
      save: 'Save',
      cancel: 'Cancel',
      noClassrooms: 'No classrooms found'
    },
    login: {
      title: 'Login',
      email: 'Email',
      password: 'Password',
      loginButton: 'Login',
      loginError: 'Login failed. Please check your credentials.'
    },
    errors: {
      required: 'This field is required',
      invalidEmail: 'Invalid email address',
      networkError: 'Network error. Please try again.',
      unauthorized: 'Unauthorized access',
      notFound: 'Resource not found',
      serverError: 'Server error. Please try again later.'
    },
    commonPhrases: {
      back: 'Back',
      unknown: 'Unknown',
      na: 'N/A',
      all: 'All',
      none: 'None',
      select: 'Select',
      optional: 'Optional',
      required: 'Required',
      confirm: 'Confirm',
      areYouSure: 'Are you sure?',
      thisActionCannotBeUndone: 'This action cannot be undone.'
    },
    components: {
      timetableGrid: {
        monday: 'Monday',
        tuesday: 'Tuesday',
        wednesday: 'Wednesday',
        thursday: 'Thursday',
        friday: 'Friday'
      },
      timetableCell: {
        lunchBreak: 'Lunch Break',
        subject: 'Subject',
        class: 'Class',
        teacher: 'Teacher'
      },
      timetableCalendar: {
        selectClass: 'Select Class',
        allClasses: 'All Classes',
        monthView: 'Month View',
        dayView: 'Day View',
        today: 'Today',
        noEntries: 'No timetable entries for this day',
        lesson: 'Lesson',
        subject: 'Subject',
        teacher: 'Teacher',
        classroom: 'Classroom',
        time: 'Time',
        lunchBreak: 'Lunch Break'
      }
    }
  },
  cs: {
    common: {
      dashboard: 'Nástěnka',
      logout: 'Odhlásit',
      loading: 'Načítání...',
      save: 'Uložit',
      cancel: 'Zrušit',
      delete: 'Smazat',
      edit: 'Upravit',
      add: 'Přidat',
      close: 'Zavřít',
      search: 'Hledat',
      filter: 'Filtr',
      actions: 'Akce',
      name: 'Název',
      email: 'Email',
      role: 'Role',
      yes: 'Ano',
      no: 'Ne'
    },
    dashboard: {
      title: 'Nástěnka',
      currentlyRunningLessons: 'Právě probíhající hodiny',
      noLessonsRunning: 'Momentálně neprobíhají žádné hodiny',
      break: 'Přestávka',
      todaysAbsentTeachers: 'Dnes nepřítomní učitelé',
      noTeachersAbsent: 'Dnes nejsou žádní nepřítomní učitelé',
      class: 'Třída',
      subject: 'Předmět',
      teacher: 'Učitel',
      classroom: 'Učebna',
      timeRange: 'Časový rozsah',
      reason: 'Důvod'
    },
    navigation: {
      schoolSettings: 'Nastavení školy',
      classes: 'Třídy',
      teachers: 'Učitelé',
      timetables: 'Rozvrhy',
      teacherDashboard: 'Nástěnka učitele',
      reportAbsence: 'Nahlásit nepřítomnost',
      viewTimetable: 'Zobrazit rozvrh',
      scholarDashboard: 'Nástěnka žáka'
    },
    schoolSettings: {
      title: 'Nastavení školy',
      back: 'Nástěnka',
      configureSettings: 'Konfigurovat nastavení školy',
      configureDescription: 'Spravujte konfiguraci rozvrhu školy včetně vyučovacích hodin, přestávek a obědů.',
      timeSettings: 'Nastavení času',
      classHourSettings: 'Nastavení vyučovacích hodin',
      breakSettings: 'Nastavení přestávek',
      lunchSettings: 'Nastavení oběda',
      startTime: 'Začátek',
      endTime: 'Konec',
      classHourLength: 'Délka vyučovací hodiny (minuty)',
      breakDuration: 'Délka přestávky (minuty)',
      breakDurations: 'Délky přestávek (minuty)',
      defaultBreakDuration: 'Výchozí délka přestávky (minuty)',
      lunchDuration: 'Délka oběda (minuty)',
      possibleLunchHours: 'Možné hodiny oběda',
      saveSettings: 'Uložit nastavení',
      saving: 'Ukládání...',
      settingsSaved: 'Nastavení bylo úspěšně uloženo',
      settingsError: 'Nepodařilo se uložit nastavení',
      schoolDayStart: 'Začátek školního dne',
      schoolDayEnd: 'Konec školního dne',
      durationOfPeriod: 'Délka každé vyučovací hodiny',
      breakAfterLesson: 'po hodině',
      addBreak: 'Přidat přestávku',
      removeBreak: 'Odstranit přestávku',
      setBreakDurations: 'Nastavte délku každé přestávky mezi hodinami. Poslední délka přestávky bude použita pro případné další přestávky.',
      fallbackDuration: 'Záložní délka, pokud není nastaveno break_durations',
      commaSeparatedHours: 'Čárkami oddělené indexy hodin, kdy je možný oběd (např. 3,4,5). Indexy hodin začínají od 1.'
    },
    classes: {
      title: 'Třídy',
      back: 'Nástěnka',
      selectClass: 'Vybrat třídu',
      selectAClass: 'Vyberte třídu...',
      timetable: 'Rozvrh',
      loadingTimetable: 'Načítání rozvrhu...',
      noTimetableAvailable: 'Pro tuto třídu není k dispozici žádný rozvrh',
      subjects: 'Předměty',
      noSubjectsAllocated: 'Této třídě nejsou přiděleny žádné předměty',
      noPrimaryTeacher: 'Není přiřazen hlavní učitel',
      manageClass: 'Spravovat třídu',
      manageSubjects: 'Spravovat předměty',
      manageSubjectAllocations: 'Spravovat přidělení předmětů pro',
      addSubjectAllocation: 'Přidat přidělení předmětu',
      selectSubject: 'Vybrat předmět',
      weeklyHours: 'Týdenní hodiny',
      yearlyHours: 'Roční hodiny',
      hoursPerWeek: 'hodin/týden',
      hoursPerWeekPlaceholder: 'Hodin týdně',
      allowMultipleInOneDay: 'Povolit více hodin v jednom dni',
      requiredConsecutiveHours: 'Požadované po sobě jdoucí hodiny',
      requiredConsecutiveHoursPlaceholder: 'Počet hodin, které musí být za sebou (volitelné)',
      teachers: 'Učitelé',
      noTeachersAssigned: 'Nejsou přiřazeni žádní učitelé',
      existingAllocations: 'Existující přidělení',
      currentSubjectAllocations: 'Aktuální přidělení předmětů',
      noAllocations: 'Nebyla nalezena žádná přidělení',
      noSubjectAllocationsYet: 'Zatím nejsou žádná přidělení předmětů',
      updateAllocation: 'Aktualizovat',
      removeAllocation: 'Odstranit',
      addAllocation: 'Přidat přidělení',
      editSubjectAllocation: 'Upravit přidělení předmětu',
      selectPrimaryTeacher: 'Vybrat hlavního učitele (volitelné)',
      primary: 'Hlavní',
      classInformation: 'Informace o třídě',
      numberOfStudents: 'Počet studentů',
      enterNumberOfStudents: 'Zadejte počet studentů',
      addClass: 'Přidat třídu',
      editClass: 'Upravit třídu',
      deleteClass: 'Smazat třídu',
      className: 'Název třídy',
      gradeLevel: 'Ročník',
      noClasses: 'Nebyly nalezeny žádné třídy'
    },
    teachers: {
      title: 'Učitelé',
      back: 'Nástěnka',
      addNewTeacher: 'Přidat nového učitele',
      fullName: 'Celé jméno',
      maxWeeklyHours: 'Maximální týdenní hodiny',
      availability: 'Dostupnost',
      availabilityFormat: 'Formát: den:hodina1,hodina2 (např. pondělí:1,2,3 úterý:1,2)',
      availabilityPlaceholder: 'Dostupnost (např. pondělí:1,2,3 úterý:1,2)',
      addTeacher: 'Přidat učitele',
      filterByTeacher: 'Filtrovat podle učitele',
      allTeachers: 'Všichni učitelé',
      todaysTimetableFor: 'Rozvrh na dnes pro',
      loadingTimetable: 'Načítání rozvrhu...',
      noLessonsToday: 'Dnes nejsou naplánovány žádné hodiny',
      absencesFor: 'Nepřítomnosti pro',
      loadingAbsences: 'Načítání nepřítomností...',
      noAbsencesReported: 'Nejsou hlášeny žádné nepřítomnosti',
      reason: 'Důvod',
      teachersList: 'Seznam učitelů',
      maxHours: 'Max. hodiny',
      subjects: 'Předměty',
      noSubjectsAssigned: 'Nejsou přiřazeny žádné předměty',
      edit: 'Upravit',
      manageSpecializations: 'Spravovat specializace',
      reportAbsence: 'Nahlásit nepřítomnost',
      delete: 'Smazat',
      subjectCapabilities: 'Schopnosti v předmětech',
      addCapability: 'Přidat schopnost',
      selectSubject: 'Vybrat předmět',
      selectGradeLevel: 'Vybrat ročník (volitelné)',
      selectClassGroup: 'Vybrat třídu (volitelné)',
      allClassesOrSelect: 'Všechny třídy (nebo vyberte konkrétní třídu)',
      isPrimary: 'Je hlavní učitel',
      editTeacher: 'Upravit učitele',
      deleteTeacher: 'Smazat učitele',
      save: 'Uložit',
      cancel: 'Zrušit',
      close: 'Zavřít',
      noTeachers: 'Nebyli nalezeni žádní učitelé',
      seeAbsences: 'Zobrazit nepřítomnosti',
      capabilities: 'Schopnosti',
      absences: 'Nepřítomnosti',
      reportAbsenceFor: 'Nahlásit nepřítomnost pro',
      dateFrom: 'Datum od',
      dateTo: 'Datum do',
      reasonOptional: 'Důvod (volitelné)',
      reasonForAbsence: 'Důvod nepřítomnosti',
      manageSpecializationsFor: 'Spravovat specializace pro',
      addNewSpecialization: 'Přidat novou specializaci',
      addSpecialization: 'Přidat specializaci',
      currentSpecializations: 'Současné specializace',
      noSpecializationsYet: 'Zatím žádné specializace',
      class: 'Třída',
      remove: 'Odstranit'
    },
    timetables: {
      title: 'Rozvrhy',
      back: 'Nástěnka',
      generateNewFixedTimetable: 'Vygenerovat nový pevný rozvrh',
      generateTimetable: 'Vygenerovat rozvrh',
      timetableName: 'Název rozvrhu',
      timetableNamePlaceholder: 'Název rozvrhu (např. Jaro 2025)',
      validFrom: 'Platný od',
      validTo: 'Platný do',
      generate: 'Vygenerovat',
      generating: 'Generování...',
      validating: 'Ověřování...',
      deleteTimetable: 'Smazat rozvrh',
      noTimetables: 'Nebyly nalezeny žádné rozvrhy',
      viewTimetable: 'Zobrazit rozvrh',
      view: 'Zobrazit',
      validate: 'Ověřit',
      delete: 'Smazat',
      calendar: 'Kalendář',
      monthView: 'Měsíční zobrazení',
      dayView: 'Denní zobrazení',
      timetablesList: 'Seznam rozvrhů',
      selectClass: 'Vybrat třídu',
      allClasses: 'Všechny třídy',
      primary: 'Hlavní',
      substitute: 'Náhradní',
      substituteForDate: 'Náhradní pro datum',
      isPrimary: 'Je hlavní',
      entries: 'záznamů',
      actions: 'Akce',
      selectTimetable: 'Vybrat rozvrh',
      noTimetableSelected: 'Není vybrán žádný rozvrh',
      loadingTimetable: 'Načítání rozvrhu...',
      loadingTimetables: 'Načítání rozvrhů...',
      fixedTimetables: 'Pevné rozvrhy',
      substituteTimetables: 'Náhradní rozvrhy',
      classTimetableCalendar: 'Kalendář rozvrhů tříd',
      valid: 'Platný',
      noValidityPeriodSet: 'Není nastaveno období platnosti',
      noFixedTimetablesFound: 'Nebyly nalezeny žádné pevné rozvrhy. Vygenerujte jeden pro začátek.',
      noSubstituteTimetablesFound: 'Nebyly nalezeny žádné náhradní rozvrhy.',
      generateSubstituteTimetable: 'Vygenerovat náhradní rozvrh',
      selectBaseTimetable: 'Vybrat základní rozvrh',
      forDate: 'Pro datum',
      noDateSpecified: 'Není specifikováno datum',
      generateSubstitute: 'Vygenerovat náhradu',
      notAvailable: 'N/A',
      timetableValid: 'Rozvrh je platný!',
      timetableValidationFailed: 'Ověření rozvrhu selhalo',
      validationError: 'Chyba ověření',
      timetableGeneratedSuccessfully: 'Rozvrh byl úspěšně vygenerován!',
      failedToGenerateTimetable: 'Nepodařilo se vygenerovat rozvrh',
      pleaseSelectBothDates: 'Prosím vyberte obě data (platný od a platný do)',
      validFromMustBeBeforeValidTo: 'Datum "platný od" musí být před datem "platný do"',
      confirmDeleteTimetable: 'Opravdu chcete smazat tento rozvrh?',
      monday: 'Pondělí',
      tuesday: 'Úterý',
      wednesday: 'Středa',
      thursday: 'Čtvrtek',
      friday: 'Pátek',
      lunchBreak: 'Oběd'
    },
    documentation: {
      title: 'Dokumentace',
      back: 'Nástěnka',
      admin: {
        title: 'Funkce správce',
        schoolSettings: {
          title: 'Nastavení školy',
          configureTimes: 'Konfigurovat začátek a konec školního dne',
          configureClassHours: 'Nastavit délku vyučovací hodiny',
          configureBreaks: 'Konfigurovat délky přestávek (podporovány proměnné přestávky)',
          configureLunch: 'Nastavit délku oběda a možné hodiny oběda'
        },
        classes: {
          title: 'Správa tříd',
          viewTimetables: 'Zobrazit rozvrhy pro každou třídu',
          manageSubjects: 'Spravovat přidělení předmětů třídám',
          assignPrimaryTeachers: 'Přiřadit hlavní učitele pro každý předmět u třídy',
          setStudentCount: 'Nastavit počet studentů na třídu'
        },
        teachers: {
          title: 'Správa učitelů',
          addEditTeachers: 'Přidávat a upravovat informace o učitelích',
          manageCapabilities: 'Spravovat schopnosti učitelů v předmětech a přiřazení tříd',
          viewAbsences: 'Zobrazit nepřítomnosti učitelů a filtrovat podle data',
          viewTimetables: 'Zobrazit denní rozvrhy učitelů'
        },
        subjects: {
          title: 'Správa předmětů',
          addEditSubjects: 'Přidávat a upravovat předměty',
          configureConstraints: 'Konfigurovat omezení předmětů (po sobě jdoucí hodiny, vícekrát denně atd.)',
          manageAllocations: 'Spravovat přidělení předmětů třídám a týdenní hodiny'
        },
        classrooms: {
          title: 'Správa učeben',
          addEditClassrooms: 'Přidávat a upravovat informace o učebnách',
          setCapacity: 'Nastavit maximální kapacitu pro každou učebnu',
          assignSpecializations: 'Přiřadit specializace předmětů učebnám'
        },
        timetables: {
          title: 'Správa rozvrhů',
          generateFixed: 'Generovat pevné (hlavní) rozvrhy pro konkrétní období',
          generateSubstitute: 'Generovat náhradní rozvrhy pro dny s nepřítomností učitelů/učeben',
          validateTimetables: 'Ověřovat rozvrhy na konflikty a porušení omezení',
          viewCalendar: 'Zobrazit rozvrhy v kalendářním formátu (měsíční a denní zobrazení)',
          deleteTimetables: 'Mazat rozvrhy (pevné i náhradní)'
        },
        dashboard: {
          title: 'Nástěnka',
          viewRunningLessons: 'Zobrazit právě probíhající hodiny ve všech třídách',
          viewAbsentTeachers: 'Zobrazit dnes nepřítomné učitele'
        },
        howTo: {
          generateTimetable: {
            title: 'Jak vygenerovat pevný rozvrh',
            step1: 'Přejděte na stránku Rozvrhy z nástěnky',
            step2: 'Klikněte na tlačítko "Vygenerovat nový pevný rozvrh"',
            step3: 'Zadejte název rozvrhu (např. "Jaro 2025")',
            step4: 'Vyberte období platnosti (datum "Platný od" a "Platný do")',
            step5: 'Klikněte na "Vygenerovat" a počkejte na vytvoření rozvrhu. Po vygenerování bude automaticky ověřen.'
          },
          assignPrimaryTeacher: {
            title: 'Jak přiřadit hlavního učitele k předmětu třídy',
            step1: 'Přejděte na stránku Třídy z nástěnky',
            step2: 'Vyberte třídu z rozbalovacího menu',
            step3: 'Klikněte na tlačítko "Spravovat předměty"',
            step4: 'Při přidávání nebo úpravě přidělení předmětu vyberte hlavního učitele z rozbalovacího menu. Hlavní učitel bude použit při generování pevných rozvrhů.'
          },
          generateSubstitute: {
            title: 'Jak vygenerovat náhradní rozvrh',
            step1: 'Ujistěte se, že máte vytvořený alespoň jeden pevný (hlavní) rozvrh',
            step2: 'Přejděte na stránku Rozvrhy a přejděte do sekce "Vygenerovat náhradní rozvrh"',
            step3: 'Vyberte základní rozvrh a zvolte datum, pro které potřebujete náhradu',
            step4: 'Klikněte na "Vygenerovat náhradu". Systém vytvoří nový rozvrh s ohledem na nepřítomnosti učitelů a učeben pro konkrétní datum.'
          }
        }
      },
      teacher: {
        title: 'Funkce učitele',
        timetable: {
          title: 'Rozvrh',
          viewDailyTimetable: 'Zobrazit svůj denní rozvrh s časy hodin, předměty, třídami a učebnami',
          viewWeeklySchedule: 'Zobrazit svůj týdenní rozvrh'
        },
        absences: {
          title: 'Nepřítomnosti',
          reportAbsence: 'Nahlásit nepřítomnosti pro konkrétní data a hodiny',
          viewAbsences: 'Zobrazit své nahlášené nepřítomnosti'
        },
        dashboard: {
          title: 'Nástěnka',
          viewTodaysSchedule: 'Zobrazit dnešní rozvrh a nadcházející hodiny',
          quickActions: 'Přístup k rychlým akcím a navigaci'
        },
        howTo: {
          viewTimetable: {
            title: 'Jak zobrazit svůj rozvrh',
            step1: 'Přejděte na stránku Učitelé z nástěnky',
            step2: 'Vyberte sebe z rozbalovacího menu učitelů',
            step3: 'V sekci "Rozvrh na dnes" uvidíte všechny své hodiny pro dnešní den s časy, předměty, třídami a učebnami.'
          },
          reportAbsence: {
            title: 'Jak nahlásit nepřítomnost',
            step1: 'Přejděte na stránku "Nahlásit nepřítomnost" z nástěnky',
            step2: 'Vyberte datum od a datum do pro vaši nepřítomnost',
            step3: 'Volitelně zadejte důvod nepřítomnosti',
            step4: 'Klikněte na "Nahlásit nepřítomnost". Po nahlášení může administrátor vygenerovat náhradní rozvrh.'
          }
        }
      }
    },
    subjects: {
      title: 'Předměty',
      back: 'Nástěnka',
      addNewSubject: 'Přidat nový předmět',
      subjectName: 'Název předmětu',
      canBeMultipleTimesPerDay: 'Může být vícekrát denně',
      mustBeConsecutive: 'Musí být po sobě jdoucí hodiny',
      consecutiveHours: 'Po sobě jdoucí hodiny',
      addSubject: 'Přidat předmět',
      subjectsList: 'Seznam předmětů',
      editSubject: 'Upravit předmět',
      deleteSubject: 'Smazat předmět',
      save: 'Uložit',
      cancel: 'Zrušit',
      noSubjects: 'Nebyly nalezeny žádné předměty'
    },
    classrooms: {
      title: 'Učebny',
      back: 'Nástěnka',
      addNewClassroom: 'Přidat novou učebnu',
      classroomName: 'Název učebny',
      specializations: 'Specializace',
      selectSpecializations: 'Vybrat specializace (více)',
      noSpecialization: 'Bez specializace',
      addClassroom: 'Přidat učebnu',
      classroomsList: 'Seznam učeben',
      editClassroom: 'Upravit učebnu',
      deleteClassroom: 'Smazat učebnu',
      save: 'Uložit',
      cancel: 'Zrušit',
      noClassrooms: 'Nebyly nalezeny žádné učebny'
    },
    login: {
      title: 'Přihlášení',
      email: 'Email',
      password: 'Heslo',
      loginButton: 'Přihlásit',
      loginError: 'Přihlášení selhalo. Zkontrolujte prosím své přihlašovací údaje.'
    },
    errors: {
      required: 'Toto pole je povinné',
      invalidEmail: 'Neplatná emailová adresa',
      networkError: 'Chyba sítě. Zkuste to prosím znovu.',
      unauthorized: 'Neautorizovaný přístup',
      notFound: 'Zdroj nenalezen',
      serverError: 'Chyba serveru. Zkuste to prosím později.'
    },
    commonPhrases: {
      back: 'Zpět',
      unknown: 'Neznámý',
      na: 'N/A',
      all: 'Vše',
      none: 'Žádné',
      select: 'Vybrat',
      optional: 'Volitelné',
      required: 'Povinné',
      confirm: 'Potvrdit',
      areYouSure: 'Jste si jisti?',
      thisActionCannotBeUndone: 'Tuto akci nelze vrátit zpět.'
    },
    components: {
      timetableGrid: {
        monday: 'Pondělí',
        tuesday: 'Úterý',
        wednesday: 'Středa',
        thursday: 'Čtvrtek',
        friday: 'Pátek'
      },
      timetableCell: {
        lunchBreak: 'Oběd',
        subject: 'Předmět',
        class: 'Třída',
        teacher: 'Učitel'
      },
      timetableCalendar: {
        selectClass: 'Vybrat třídu',
        allClasses: 'Všechny třídy',
        monthView: 'Měsíční zobrazení',
        dayView: 'Denní zobrazení',
        today: 'Dnes',
        noEntries: 'Pro tento den nejsou žádné záznamy rozvrhu',
        lesson: 'Hodina',
        subject: 'Předmět',
        teacher: 'Učitel',
        classroom: 'Učebna',
        time: 'Čas',
        lunchBreak: 'Oběd'
      }
    }
  }
}

export const useI18nStore = defineStore('i18n', () => {
  const currentLanguage = ref<Language>(
    (localStorage.getItem('language') as Language) || 'en'
  )

  const t = computed(() => {
    return (key: string): string => {
      const keys = key.split('.')
      let value: any = translations[currentLanguage.value]
      
      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = value[k]
        } else {
          return key // Return key if translation not found
        }
      }
      
      return typeof value === 'string' ? value : key
    }
  })

  function setLanguage(lang: Language) {
    currentLanguage.value = lang
    localStorage.setItem('language', lang)
  }

  function getCurrentLanguage(): Language {
    return currentLanguage.value
  }

  return {
    currentLanguage,
    t,
    setLanguage,
    getCurrentLanguage
  }
})

