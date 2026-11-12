/* AMSDP shared i18n — centralized Bangla/English dictionaries. */
export const DICT = {
  bn: {
    app: 'AMSDP', dash: 'ড্যাশবোর্ড', welcome: 'স্বাগতম', role: 'ভূমিকা', logout: 'লগআউট',
    loginRequired: 'লগইন প্রয়োজন', goLogin: 'লগইন পৃষ্ঠায় যান', org: 'প্রতিষ্ঠান',
    branches: 'শাখা', branch: 'শাখা', patients: 'রোগী', doctors: 'ডাক্তার', staff: 'স্টাফ',
    schedules: 'শিডিউল', appointments: 'অ্যাপয়েন্টমেন্ট', queue: 'কিউ', audit: 'অডিট',
    loading: 'লোড হচ্ছে...', empty: 'কোনো তথ্য নেই', error: 'ত্রুটি', retry: 'আবার চেষ্টা করুন',
    permissionDenied: 'অনুমতি নেই', save: 'সংরক্ষণ', cancel: 'বাতিল', confirm: 'নিশ্চিত',
    actions: 'কর্ম', search: 'অনুসন্ধান', date: 'তারিখ', time: 'সময়', status: 'অবস্থা',
    token: 'টোকেন', position: 'অবস্থান', name: 'নাম', mobile: 'মোবাইল', room: 'কক্ষ', doctor: 'ডাক্তার',
    select: 'নির্বাচন করুন', policy: 'নীতি', submit: 'জমা দিন',
    booked: 'বুকিং হয়েছে', checkedIn: 'চেক-ইন হয়েছে', waiting: 'অপেক্ষমাণ',
    completedT: 'সম্পন্ন', cancelledT: 'বাতিল হয়েছে', noShow: 'অনুপস্থিত',
    action: 'কর্ম', entity: 'এনটিটি', before: 'আগে', after: 'পরে', reason: 'কারণ',
    patient: 'রোগী', speciality: 'বিশেষত্ব', qualification: 'যোগ্যতা', roleLabel: 'ভূমিকা',
    callNext: 'পরবর্তী কল করুন', startConsult: 'পরামর্শ শুরু করুন', completeConsult: 'পরামর্শ সম্পন্ন করুন',
    checkIn: 'চেক-ইন', walkIn: 'ওয়াক-ইন', source: 'উৎস', start: 'শুরু করুন', complete: 'সম্পন্ন করুন',
    waitingKey: 'অপেক্ষমাণ', calledKey: 'কল করা হয়েছে', inConsultationKey: 'পরামর্শ চলছে',
    skippedKey: 'বাদ দেওয়া', completedKey: 'সম্পন্ন', cancelledKey: 'বাতিল', noShowKey: 'অনুপস্থিত',
    notifications: 'নোটিফিকেশন', notificationSettings: 'নোটিফিকেশন সেটিংস',
    notificationHint: 'অ্যাপয়েন্টমেন্ট নিশ্চিতকরণ ও রিমাইন্ডারের জন্য হোয়াটসঅ্যাপ ও এসএমএস বার্তা।',
    missedTurn: 'টার্ন মিস', missedTurnTitle: 'টার্ন মিস রেকর্ড করুন',
    missedTurnMsg: 'ডাকা হলে রোগী সাড়া দেননি। টোকেন ও অ্যাপয়েন্টমেন্ট অপরিবর্তিত থাকবে।',
    missedTurnRecorded: 'টার্ন মিস রেকর্ড হয়েছে — রোগী পুনরুদ্ধারের অপেক্ষায়।',
    recover: 'পুনরুদ্ধার', recoverTitle: 'রোগী পুনরুদ্ধার করুন',
    recoverMsg: 'একই টোকেন ও অ্যাপয়েন্টমেন্ট থাকবে; শুধু কিউ অবস্থান পরিবর্তন হবে।',
    recoveryMode: 'পুনঃপ্রবেশ স্থান', endOfQueue: 'কিউয়ের শেষে', atPosition: 'অবস্থানে',
    recoveryReason: 'কারণ', recoveredNotice: 'রোগী পুনরুদ্ধার হয়েছে।',
    awaitingRecovery: 'পুনরুদ্ধারের অপেক্ষায়', pleaseWait: 'অপেক্ষা করুন...',
    channel: 'চ্যানেল', enabled: 'চালু', provider: 'প্রোভাইডার',
    reminderTiming: 'রিমাইন্ডারের সময়', minutesBefore: 'মিনিট আগে',
    providerStatus: 'প্রোভাইডার অবস্থা', last24h: 'শেষ ২৪ ঘণ্টা',
    sent: 'পাঠানো হয়েছে', delivered: 'ডেলিভার হয়েছে', pendingT: 'অপেক্ষমাণ', failed: 'ব্যর্থ',
    latestMessage: 'সর্বশেষ বার্তা', integrationStatus: 'ইন্টিগ্রেশন',
    mockOnly: 'শুধু মক — কোনো লাইভ হোয়াটসঅ্যাপ/এসএমএস প্রোভাইডার কনফিগার করা নেই।',
    credentialsNote: 'প্রোভাইডার ক্রেডেনশিয়াল সার্ভারে সংরক্ষিত থাকে, কখনো দেখানো হয় না।',
    platformProviders: 'উপলব্ধ প্রোভাইডার', savedChanges: 'সেটিংস সংরক্ষিত হয়েছে।',
    settingsFor: 'সেটিংস —', lastAttempt: 'সর্বশেষ চেষ্টা', total: 'মোট', lifetime: 'সর্বমোট',
  },
  en: {
    app: 'AMSDP', dash: 'Dashboard', welcome: 'Welcome', role: 'Role', logout: 'Logout',
    loginRequired: 'Login Required', goLogin: 'Go to login', org: 'Organization',
    branches: 'Branches', branch: 'Branch', patients: 'Patients', doctors: 'Doctors', staff: 'Staff',
    schedules: 'Schedules', appointments: 'Appointments', queue: 'Queue', audit: 'Audit',
    loading: 'Loading...', empty: 'No data', error: 'Error', retry: 'Retry',
    permissionDenied: 'Permission denied', save: 'Save', cancel: 'Cancel', confirm: 'Confirm',
    actions: 'Actions', search: 'Search', date: 'Date', time: 'Time', status: 'Status',
    token: 'Token', position: 'Position', name: 'Name', mobile: 'Mobile', room: 'Room', doctor: 'Doctor',
    select: 'Select', policy: 'Policy', submit: 'Save',
    booked: 'Booked', checkedIn: 'Checked-in', waiting: 'Waiting',
    completedT: 'Completed', cancelledT: 'Cancelled', noShow: 'No-show',
    action: 'Action', entity: 'Entity', before: 'Before', after: 'After', reason: 'Reason',
    patient: 'Patient', speciality: 'Speciality', qualification: 'Qualification', roleLabel: 'Role',
    callNext: 'Call Next', startConsult: 'Start Consultation', completeConsult: 'Complete Consultation',
    checkIn: 'Check-in', walkIn: 'Walk-in', source: 'Source', start: 'Start', complete: 'Complete',
    waitingKey: 'Waiting', calledKey: 'Called', inConsultationKey: 'In Consultation',
    skippedKey: 'Skipped', completedKey: 'Completed', cancelledKey: 'Cancelled', noShowKey: 'No-Show',
    notifications: 'Notifications', notificationSettings: 'Notification settings',
    notificationHint: 'WhatsApp and SMS messages for appointment confirmation and reminders.',
    missedTurn: 'Missed turn', missedTurnTitle: 'Record missed turn',
    missedTurnMsg: 'The patient did not respond when called. The token and appointment are kept.',
    missedTurnRecorded: 'Missed turn recorded — the patient awaits recovery.',
    recover: 'Recover', recoverTitle: 'Recover patient',
    recoverMsg: 'The same token and appointment are kept; only the queue position changes.',
    recoveryMode: 'Re-entry point', endOfQueue: 'End of queue', atPosition: 'At position',
    recoveryReason: 'Reason', recoveredNotice: 'Patient recovered.',
    awaitingRecovery: 'Awaiting recovery', pleaseWait: 'Please wait...',
    channel: 'Channel', enabled: 'Enabled', provider: 'Provider',
    reminderTiming: 'Reminder timing', minutesBefore: 'minutes before',
    providerStatus: 'Provider status', last24h: 'Last 24 hours',
    sent: 'Sent', delivered: 'Delivered', pendingT: 'Pending', failed: 'Failed',
    latestMessage: 'Latest message', integrationStatus: 'Integration',
    mockOnly: 'Mock only — no live WhatsApp/SMS provider is configured.',
    credentialsNote: 'Provider credentials are held server-side and are never displayed.',
    platformProviders: 'Available providers', savedChanges: 'Settings saved.',
    settingsFor: 'Settings —', lastAttempt: 'Last attempt', total: 'Total', lifetime: 'Lifetime',
  },
};

export function getLocale() {
  if (typeof window === 'undefined') return 'bn';
  return sessionStorage.getItem('locale') || 'bn';
}

export function setLocale(l) {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem('locale', l);
}

export function t(key) {
  const l = getLocale();
  const table = DICT[l] || DICT.bn;
  return table[key] || DICT.bn[key] || key;
}

export function fmtDate(iso) {
  if (!iso) return '';
  try {
    return new Intl.DateTimeFormat(getLocale() === 'bn' ? 'bn-BD' : 'en-GB',
      { year: 'numeric', month: 'short', day: 'numeric' }).format(new Date(iso));
  } catch (e) { return String(iso); }
}