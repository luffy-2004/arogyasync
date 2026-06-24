import { createContext, useState, useEffect, useCallback } from 'react';
import { authApi, consultationsApi, patientsApi, prescriptionsApi, syncApi, vaccinationsApi } from '../services/api';

export const SyncContext = createContext();

const normalizePatient = (item) => ({
  id: item.id,
  name: item.name,
  age: item.age,
  gender: item.gender,
  phone: item.phone || '',
  address: item.address || '',
  status: 'Synced',
  timestamp: new Date(item.created_at).toLocaleDateString('en-GB'),
});

const normalizeConsultation = (item) => ({
  id: item.id,
  patientName: item.patient_id,
  symptoms: item.symptoms || '',
  diagnosis: item.diagnosis || '',
  doctorNotes: item.doctor_notes || '',
  doctor: 'Dr. Anjali Sharma',
  status: 'Synced',
  timestamp: new Date(item.created_at).toLocaleDateString('en-GB'),
});

const normalizePrescription = (item) => ({
  id: item.id,
  patientName: item.consultation_id,
  consultationId: item.consultation_id,
  medicine: item.medicine_name,
  dosage: item.dosage,
  duration: item.duration || '',
  status: 'Synced',
  timestamp: new Date(item.created_at).toLocaleDateString('en-GB'),
});

const normalizeVaccination = (item) => ({
  id: item.id,
  patientName: item.patient_id,
  vaccine: item.vaccine_name,
  batch: '',
  vaccinationDate: item.vaccination_date,
  vacStatus: item.status,
  status: 'Synced',
  timestamp: new Date(item.created_at).toLocaleDateString('en-GB'),
});

export const SyncProvider = ({ children }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingSync, setPendingSync] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState('Not synced yet');
  const [totalPatients, setTotalPatients] = useState(0);
  const [todayVisits, setTodayVisits] = useState(0);

  const [patientsCount, setPatientsCount] = useState(0);
  const [consultationsCount, setConsultationsCount] = useState(0);
  const [prescriptionsCount, setPrescriptionsCount] = useState(0);
  const [vaccinationsCount, setVaccinationsCount] = useState(0);

  const [patientsList, setPatientsList] = useState([]);
  const [consultationsList, setConsultationsList] = useState([]);
  const [prescriptionsList, setPrescriptionsList] = useState([]);
  const [vaccinationsList, setVaccinationsList] = useState([]);
  const [syncLogs, setSyncLogs] = useState([]);
  const [syncQueue, setSyncQueue] = useState([]);

  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [isSyncing, setIsSyncing] = useState(false);

  const [currentTime, setCurrentTime] = useState(() => {
    const n = new Date(); let h = n.getHours(), m = n.getMinutes(), ap = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12; return `${h}:${m < 10 ? '0' + m : m} ${ap}`;
  });

  const [currentDate] = useState(() =>
    new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  );

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    window.setTimeout(() => setToast((p) => ({ ...p, show: false })), 3500);
  };

  const loadData = useCallback(async () => {
    try {
      const [patientsResponse, consultationsResponse] = await Promise.all([
        patientsApi.list({ limit: 100 }),
        consultationsApi.list({ limit: 100 }),
      ]);

      const patients = (patientsResponse?.items || []).map(normalizePatient);
      const consultations = (consultationsResponse?.items || []).map(normalizeConsultation);
      const consultationIds = consultations.map((item) => item.id);
      const patientIds = patients.map((item) => item.id);

      const [prescriptionResponses, vaccinationResponses] = await Promise.all([
        Promise.all(consultationIds.map((id) => prescriptionsApi.listByConsultation(id).catch(() => []))),
        Promise.all(patientIds.map((id) => vaccinationsApi.listByPatient(id).catch(() => []))),
      ]);

      const prescriptions = prescriptionResponses.flat().map(normalizePrescription);
      const vaccinations = vaccinationResponses.flat().map(normalizeVaccination);

      setPatientsList(patients);
      setConsultationsList(consultations);
      setPrescriptionsList(prescriptions);
      setVaccinationsList(vaccinations);
      setPatientsCount(patients.length);
      setTotalPatients(patients.length);
      setConsultationsCount(consultations.length);
      setTodayVisits(consultations.length);
      setPrescriptionsCount(prescriptions.length);
      setVaccinationsCount(vaccinations.length);
    } catch (error) {
      showToast(error.message || 'Unable to load records');
    }
  }, []);

  useEffect(() => {
    let d = new Date();
    const t = window.setInterval(() => {
      d.setSeconds(d.getSeconds() + 1);
      let h = d.getHours(), m = d.getMinutes(), ap = h >= 12 ? 'PM' : 'AM';
      h = h % 12 || 12; setCurrentTime(`${h}:${m < 10 ? '0' + m : m} ${ap}`);
    }, 1000);
    return () => window.clearInterval(t);
  }, []);

  useEffect(() => {
    const onLine = () => setIsOnline(true);
    const offLine = () => setIsOnline(false);
    window.addEventListener('online', onLine);
    window.addEventListener('offline', offLine);
    return () => {
      window.removeEventListener('online', onLine);
      window.removeEventListener('offline', offLine);
    };
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (!token) return;
    loadData();
  }, [loadData]);

  const refreshSyncState = async () => {
    try {
      const [queueResponse, statusResponse] = await Promise.all([syncApi.queue({ limit: 100 }), syncApi.status()]);
      const queueItems = (queueResponse || []).map((item) => ({
        entityType: item.entity_type,
        operation: item.operation_type,
        syncStatus: item.sync_status,
        timestamp: new Date(item.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        errorMessage: item.error_message || '',
      }));
      setSyncQueue(queueItems);
      setPendingSync(queueItems.filter((item) => item.syncStatus === 'PENDING').length);
      setLastSyncTime(statusResponse?.cloud_connected ? 'Connected' : 'Offline');
    } catch {
      setLastSyncTime('Unavailable');
    }
  };

  const addPatient = async (details) => {
    try {
      const created = await patientsApi.create({
        name: details.name,
        age: Number(details.age),
        gender: details.gender,
        phone: details.phone || null,
        address: details.address || null,
      });
      const normalized = normalizePatient(created);
      setPatientsList((p) => [normalized, ...p]);
      setTotalPatients((p) => p + 1);
      setPatientsCount((p) => p + 1);
      showToast(`Patient "${details.name}" created.`);
      await refreshSyncState();
    } catch (error) {
      showToast(error.message || 'Unable to create patient');
    }
  };

  const editPatient = async (id, details) => {
    try {
      const updated = await patientsApi.update(id, {
        name: details.name,
        age: Number(details.age),
        gender: details.gender,
        phone: details.phone || null,
        address: details.address || null,
      });
      const normalized = normalizePatient(updated);
      setPatientsList((p) => p.map((pt) => (pt.id === id ? normalized : pt)));
      showToast('Patient updated.');
    } catch (error) {
      showToast(error.message || 'Unable to update patient');
    }
  };

  const deletePatient = async (id) => {
    try {
      await patientsApi.remove(id);
      setPatientsList((p) => p.filter((pt) => pt.id !== id));
      setTotalPatients((p) => Math.max(0, p - 1));
      setPatientsCount((p) => Math.max(0, p - 1));
      showToast('Patient deleted.');
    } catch (error) {
      showToast(error.message || 'Unable to delete patient');
    }
  };

  const addConsultation = async (details) => {
    try {
      const created = await consultationsApi.create({
        patient_id: details.patient_id,
        symptoms: details.symptoms || '',
        diagnosis: details.diagnosis,
        doctor_notes: details.doctorNotes || '',
      });
      const normalized = normalizeConsultation(created);
      setConsultationsList((p) => [normalized, ...p]);
      setConsultationsCount((p) => p + 1);
      setTodayVisits((p) => p + 1);
      showToast('Consultation saved.');
      await refreshSyncState();
    } catch (error) {
      showToast(error.message || 'Unable to create consultation');
    }
  };

  const editConsultation = async (id, details) => {
    try {
      const updated = await consultationsApi.update(id, {
        symptoms: details.symptoms || '',
        diagnosis: details.diagnosis,
        doctor_notes: details.doctorNotes || '',
      });
      const normalized = normalizeConsultation(updated);
      setConsultationsList((p) => p.map((c) => (c.id === id ? normalized : c)));
      showToast('Consultation updated.');
    } catch (error) {
      showToast(error.message || 'Unable to update consultation');
    }
  };

  const addPrescription = async (details) => {
    try {
      const created = await prescriptionsApi.create({
        consultation_id: details.consultationId,
        medicine_name: details.medicine,
        dosage: details.dosage,
        duration: details.duration || '',
      });
      const normalized = normalizePrescription(created);
      setPrescriptionsList((p) => [normalized, ...p]);
      setPrescriptionsCount((p) => p + 1);
      showToast('Prescription saved.');
      await refreshSyncState();
    } catch (error) {
      showToast(error.message || 'Unable to create prescription');
    }
  };

  const editPrescription = async (id, details) => {
    try {
      const updated = await prescriptionsApi.update(id, {
        medicine_name: details.medicine,
        dosage: details.dosage,
        duration: details.duration || '',
      });
      const normalized = normalizePrescription(updated);
      setPrescriptionsList((p) => p.map((r) => (r.id === id ? normalized : r)));
      showToast('Prescription updated.');
    } catch (error) {
      showToast(error.message || 'Unable to update prescription');
    }
  };

  const addVaccination = async (details) => {
    try {
      const created = await vaccinationsApi.create({
        patient_id: details.patient_id,
        vaccine_name: details.vaccine,
        vaccination_date: details.vaccinationDate,
        status: details.vacStatus || 'Administered',
      });
      const normalized = normalizeVaccination(created);
      setVaccinationsList((p) => [normalized, ...p]);
      setVaccinationsCount((p) => p + 1);
      showToast('Vaccination recorded.');
      await refreshSyncState();
    } catch (error) {
      showToast(error.message || 'Unable to create vaccination');
    }
  };

  const editVaccination = async (id, details) => {
    try {
      const updated = await vaccinationsApi.update(id, {
        vaccine_name: details.vaccine,
        vaccination_date: details.vaccinationDate,
        status: details.vacStatus || 'Administered',
      });
      const normalized = normalizeVaccination(updated);
      setVaccinationsList((p) => p.map((v) => (v.id === id ? normalized : v)));
      showToast('Vaccination updated.');
    } catch (error) {
      showToast(error.message || 'Unable to update vaccination');
    }
  };

  const performSync = async () => {
    if (isSyncing || !isOnline) return;
    setIsSyncing(true);
    try {
      const response = await syncApi.trigger();
      const ts = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
      setLastSyncTime(ts);
      setSyncLogs((p) => [{ id: p.length + 1, type: 'success', title: 'Sync completed', desc: response?.message || 'Sync completed.', time: ts }, ...p]);
      await refreshSyncState();
      showToast('Sync completed.');
    } catch (error) {
      showToast(error.message || 'Sync failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const retryFailed = async () => {
    try {
      const response = await syncApi.retryFailed();
      showToast(response?.message || 'Retry completed');
      await refreshSyncState();
    } catch (error) {
      showToast(error.message || 'Unable to retry sync');
    }
  };

  useEffect(() => {
    if (isOnline && !isSyncing) {
      refreshSyncState();
    }
  }, [isOnline, isSyncing]);

  return (
    <SyncContext.Provider value={{
      isOnline, pendingSync, lastSyncTime, totalPatients, todayVisits,
      patientsCount, consultationsCount, prescriptionsCount, vaccinationsCount,
      patientsList, consultationsList, prescriptionsList, vaccinationsList,
      syncLogs, syncQueue, toast, isSyncing, currentTime, currentDate,
      toggleConnection: () => {
        const next = !isOnline;
        setIsOnline(next);
        showToast(next ? 'System is now Online.' : 'System is now Offline.');
      },
      addPatient, editPatient, deletePatient,
      addConsultation, editConsultation,
      addPrescription, editPrescription,
      addVaccination, editVaccination,
      performSync, retryFailed, showToast,
    }}>
      {children}
    </SyncContext.Provider>
  );
};