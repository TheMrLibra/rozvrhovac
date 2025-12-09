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
      generalSettings: 'General Settings',
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
      settingsError: 'Failed to save settings'
    },
    classes: {
      title: 'Classes',
      addClass: 'Add Class',
      editClass: 'Edit Class',
      deleteClass: 'Delete Class',
      className: 'Class Name',
      gradeLevel: 'Grade Level',
      subjects: 'Subjects',
      teachers: 'Teachers',
      timetable: 'Timetable',
      noClasses: 'No classes found',
      weeklyHours: 'Weekly Hours',
      yearlyHours: 'Yearly Hours'
    },
    teachers: {
      title: 'Teachers',
      addTeacher: 'Add Teacher',
      editTeacher: 'Edit Teacher',
      deleteTeacher: 'Delete Teacher',
      fullName: 'Full Name',
      maxWeeklyHours: 'Max Weekly Hours',
      availability: 'Availability',
      capabilities: 'Capabilities',
      absences: 'Absences',
      noTeachers: 'No teachers found',
      filterByTeacher: 'Filter by Teacher',
      seeAbsences: 'See Absences'
    },
    timetables: {
      title: 'Timetables',
      generateTimetable: 'Generate Timetable',
      timetableName: 'Timetable Name',
      validFrom: 'Valid From',
      validTo: 'Valid To',
      generate: 'Generate',
      validating: 'Validating...',
      deleteTimetable: 'Delete Timetable',
      noTimetables: 'No timetables found',
      viewTimetable: 'View Timetable',
      calendar: 'Calendar',
      monthView: 'Month View',
      dayView: 'Day View'
    },
    subjects: {
      title: 'Subjects',
      addSubject: 'Add Subject',
      editSubject: 'Edit Subject',
      deleteSubject: 'Delete Subject',
      subjectName: 'Subject Name',
      canBeMultipleTimesPerDay: 'Can be multiple times per day',
      mustBeConsecutive: 'Must be consecutive hours',
      consecutiveHours: 'Consecutive Hours',
      noSubjects: 'No subjects found'
    },
    classrooms: {
      title: 'Classrooms',
      addClassroom: 'Add Classroom',
      editClassroom: 'Edit Classroom',
      deleteClassroom: 'Delete Classroom',
      classroomName: 'Classroom Name',
      specializations: 'Specializations',
      noClassrooms: 'No classrooms found',
      noSpecialization: 'No specialization'
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
      generalSettings: 'Obecná nastavení',
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
      settingsError: 'Nepodařilo se uložit nastavení'
    },
    classes: {
      title: 'Třídy',
      addClass: 'Přidat třídu',
      editClass: 'Upravit třídu',
      deleteClass: 'Smazat třídu',
      className: 'Název třídy',
      gradeLevel: 'Ročník',
      subjects: 'Předměty',
      teachers: 'Učitelé',
      timetable: 'Rozvrh',
      noClasses: 'Nebyly nalezeny žádné třídy',
      weeklyHours: 'Týdenní hodiny',
      yearlyHours: 'Roční hodiny'
    },
    teachers: {
      title: 'Učitelé',
      addTeacher: 'Přidat učitele',
      editTeacher: 'Upravit učitele',
      deleteTeacher: 'Smazat učitele',
      fullName: 'Celé jméno',
      maxWeeklyHours: 'Maximální týdenní hodiny',
      availability: 'Dostupnost',
      capabilities: 'Schopnosti',
      absences: 'Nepřítomnosti',
      noTeachers: 'Nebyli nalezeni žádní učitelé',
      filterByTeacher: 'Filtrovat podle učitele',
      seeAbsences: 'Zobrazit nepřítomnosti'
    },
    timetables: {
      title: 'Rozvrhy',
      generateTimetable: 'Vygenerovat rozvrh',
      timetableName: 'Název rozvrhu',
      validFrom: 'Platný od',
      validTo: 'Platný do',
      generate: 'Vygenerovat',
      validating: 'Ověřování...',
      deleteTimetable: 'Smazat rozvrh',
      noTimetables: 'Nebyly nalezeny žádné rozvrhy',
      viewTimetable: 'Zobrazit rozvrh',
      calendar: 'Kalendář',
      monthView: 'Měsíční zobrazení',
      dayView: 'Denní zobrazení'
    },
    subjects: {
      title: 'Předměty',
      addSubject: 'Přidat předmět',
      editSubject: 'Upravit předmět',
      deleteSubject: 'Smazat předmět',
      subjectName: 'Název předmětu',
      canBeMultipleTimesPerDay: 'Může být vícekrát denně',
      mustBeConsecutive: 'Musí být po sobě jdoucí hodiny',
      consecutiveHours: 'Po sobě jdoucí hodiny',
      noSubjects: 'Nebyly nalezeny žádné předměty'
    },
    classrooms: {
      title: 'Učebny',
      addClassroom: 'Přidat učebnu',
      editClassroom: 'Upravit učebnu',
      deleteClassroom: 'Smazat učebnu',
      classroomName: 'Název učebny',
      specializations: 'Specializace',
      noClassrooms: 'Nebyly nalezeny žádné učebny',
      noSpecialization: 'Bez specializace'
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

