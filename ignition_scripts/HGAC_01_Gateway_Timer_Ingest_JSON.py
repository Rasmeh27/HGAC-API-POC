from java.io import File

TAG_PROVIDER = "[default]"
BASE = TAG_PROVIDER + "HGAC/HainaOccidental/Entrada/Gate1/Lane1"

FILES = {
	"BioStar": "C:\\Users\\Public\\hgac_biostar_local.json",
	"RFID": "C:\\Users\\Public\\hgac_rfid.json",
	"RNTT": "C:\\Users\\Public\\hgac_rntt_combinado.json",
	"Navis": "C:\\Users\\Public\\hgac_navis.json",
	"Wialon": "C:\\Users\\Public\\hgac_wialon.json",
	"LPR": "C:\\Users\\Public\\hgac_lpr.json",
}
LPR_EVENT_DIR = "C:\\Users\\Public\\hgac_lpr_events"

def now_text():
	return system.date.format(system.date.now(), "yyyy-MM-dd HH:mm:ss")

def read_json_file(path):
	try:
		if not File(path).exists():
			return None, "FILE_NOT_FOUND"
		text = system.file.readFileAsString(path)
		if text is None or len(text.strip()) == 0:
			return None, "EMPTY_FILE"
		return system.util.jsonDecode(text), "OK"
	except Exception as exc:
		return None, "ERROR: %s" % str(exc)

def read_oldest_lpr_event():
	directory = File(LPR_EVENT_DIR)
	if directory.exists() and directory.isDirectory():
		files = []
		for item in directory.listFiles() or []:
			if item.isFile() and item.getName().lower().endswith(".json"):
				files.append(item)
		files.sort(key=lambda item: item.getName())
		if len(files) > 0:
			data, status = read_json_file(files[0].getAbsolutePath())
			return data, status, files[0]
	data, status = read_json_file(FILES["LPR"])
	return data, status, None

def write_tags(relative_paths, values):
	paths = []
	for rel in relative_paths:
		paths.append(BASE + "/" + rel)
	return system.tag.writeBlocking(paths, values)

def get_any(data, keys, default=None):
	if data is None:
		return default
	for key in keys:
		try:
			if key in data and data[key] is not None:
				return data[key]
		except:
			pass
	return default

def get_nested(data, path, default=None):
	try:
		cur = data
		for key in path:
			if cur is None:
				return default
			cur = cur[key]
		if cur is None:
			return default
		return cur
	except:
		return default

def clean(value):
	if value is None:
		return ""
	return str(value).strip()

def driver_full_name(driver):
	first = clean(get_any(driver, ["NAMEFIRST", "DriverFirstName"], ""))
	last = clean(get_any(driver, ["NAMELAST", "DriverLastName"], ""))
	return (first + " " + last).strip()

def parse_date(value):
	if value is None or clean(value) == "":
		return None
	for pattern in ["yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd"]:
		try:
			return system.date.parse(clean(value), pattern)
		except:
			pass
	return None

def parse_lpr_timestamp(value):
	if value is None or clean(value) == "":
		return None
	text = clean(value).replace("Z", "")
	try:
		if "." in text:
			date_part, fraction = text.split(".", 1)
			text = date_part + "." + (fraction + "000")[:3]
			return system.date.parse(text, "yyyy-MM-dd'T'HH:mm:ss.SSS")
		return system.date.parse(text, "yyyy-MM-dd'T'HH:mm:ss")
	except:
		return parse_date(value)

def is_expired(value):
	dt = parse_date(value)
	if dt is None:
		return False
	return dt.before(system.date.now())

def interpret_driver(driver):
	bdgsts = clean(get_any(driver, ["bdgsts", "DriverBdgsts"], ""))
	reasons = []
	if is_expired(get_any(driver, ["ExpiracionLicencia", "DriverLicenseExpiration"], "")):
		reasons.append("licencia vencida")
	if is_expired(get_any(driver, ["ENDDATE", "DriverAffiliationExpiration"], "")):
		reasons.append("afiliacion vencida")
	if bdgsts in ["1", "7"]:
		reasons.append("evaluacion vencida")
	elif bdgsts == "9" and len(reasons) == 0:
		reasons.append("estado bruto restringido")
	if len(reasons) > 0:
		return "Restringido", "; ".join(reasons)
	if bdgsts == "0":
		return "Activo", "bdgsts=0 (Activo); fechas vigentes"
	return "Pendiente catalogo", "bdgsts=%s" % bdgsts

def driver_bdgsts_text(driver):
	bdgsts = clean(get_any(driver, ["bdgsts", "DriverBdgsts"], ""))
	if bdgsts == "0":
		return "Activo"
	if bdgsts in ["1", "7"]:
		return "Restringido - Evaluacion vencida"
	if bdgsts == "9":
		return "Restringido"
	return "Pendiente catalogo oficial"

def interpret_truck(truck):
	estado = clean(get_any(truck, ["Estado", "TruckEstado"], ""))
	if estado == "2":
		return "Activo", "Estado=2 observado en portal RNTT como Activo"
	if estado == "5":
		return "Cancelado", "Estado=5 observado en portal RNTT como Cancelado"
	return "Pendiente catalogo", "Estado=%s" % estado

def ingest_biostar():
	data, status = read_json_file(FILES["BioStar"])
	if status != "OK":
		write_tags(["BioStar/CommStatus", "BioStar/LastUpdate"], [status, now_text()])
		return

	decision = get_any(data, ["decision_sugerida", "decision", "Decision", "estado_decision"], "")
	pasa = bool(get_any(data, ["permitir_paso", "pasa", "Pasa"], False)) or str(decision).upper() in ["PASA", "PERMITIR"]
	event_text = get_any(data, ["event_type_display", "event_text", "EventoTexto", "event_type", "event"], "")
	method = get_any(data, ["method", "Metodo", "auth_method"], "")
	if not method:
		creds = get_any(data, ["credentials"], {}) or {}
		method = get_any(creds, ["event_method"], "")
	credentials = get_any(data, ["credentials"], {}) or {}
	device = get_any(data, ["device"], {}) or {}

	write_tags(
		[
			"BioStar/Trigger",
			"BioStar/Pasa",
			"BioStar/Decision",
			"BioStar/Estado",
			"BioStar/Motivo",
			"BioStar/Metodo",
			"BioStar/EventoCodigo",
			"BioStar/EventoTexto",
			"BioStar/EventoFecha",
			"BioStar/UsuarioId",
			"BioStar/UsuarioNombre",
			"BioStar/DispositivoId",
			"BioStar/DispositivoNombre",
			"BioStar/DispositivoIp",
			"BioStar/TieneTarjeta",
			"BioStar/TieneHuella",
			"BioStar/TieneRostro",
			"BioStar/RawJson",
			"BioStar/LastUpdate",
			"BioStar/CommStatus",
		],
		[
			True,
			pasa,
			decision,
			get_any(data, ["estado", "Estado"], ""),
			get_any(data, ["motivo", "Motivo"], ""),
			method,
			str(get_any(data, ["event_type_code", "event_code", "EventoCodigo", "code"], "")),
			event_text,
			get_any(data, ["event_time", "EventoFecha", "timestamp"], now_text()),
			str(get_any(data, ["user_id", "UsuarioId"], "")),
			get_any(data, ["nombre", "user_name", "UsuarioNombre", "user"], ""),
			str(get_any(device, ["id"], get_any(data, ["device_id", "DispositivoId"], ""))),
			get_any(device, ["name"], get_any(data, ["device_name", "DispositivoNombre"], "")),
			get_any(device, ["ip"], get_any(data, ["device_ip", "DispositivoIp"], "")),
			bool(get_any(credentials, ["has_card"], get_any(data, ["has_card", "TieneTarjeta"], False))) or "CARD" in str(method).upper() or "CARD" in str(event_text).upper(),
			bool(get_any(credentials, ["has_fingerprint"], get_any(data, ["has_fingerprint", "TieneHuella"], False))) or "FINGER" in str(method).upper() or "FINGERPRINT" in str(event_text).upper(),
			bool(get_any(credentials, ["has_face"], get_any(data, ["has_face", "TieneRostro"], False))) or "FACE" in str(method).upper() or "FACE" in str(event_text).upper(),
			system.util.jsonEncode(data),
			now_text(),
			"OK",
		],
	)

def ingest_rntt():
	data, status = read_json_file(FILES["RNTT"])
	if status != "OK":
		write_tags(["RNTT/CommStatus", "RNTT/LastUpdate"], [status, now_text()])
		return

	driver = get_any(data, ["driver", "chofer", "Driver"], {}) or {}
	truck = get_any(data, ["truck", "camion", "Truck"], {}) or {}

	driver_status, driver_reason = interpret_driver(driver) if driver else ("", "")
	truck_status, truck_reason = interpret_truck(truck) if truck else ("", "")
	authorized = (not driver or str(driver_status).upper() == "ACTIVO") and (not truck or str(truck_status).upper() == "ACTIVO")

	write_tags(
		[
			"RNTT/Trigger",
			"RNTT/Found",
			"RNTT/Authorized",
			"RNTT/Status",
			"RNTT/DriverRnttCode",
			"RNTT/DriverFullName",
			"RNTT/DriverCedula",
			"RNTT/DriverLicense",
			"RNTT/DriverLicenseType",
			"RNTT/DriverLicenseExpiration",
			"RNTT/DriverAffiliationExpiration",
			"RNTT/DriverRotulo",
			"RNTT/DriverCompany",
			"RNTT/DriverBdgsts",
			"RNTT/DriverBdgstsText",
			"RNTT/DriverInterpretedStatus",
			"RNTT/DriverInterpretedReason",
			"RNTT/TruckName",
			"RNTT/TruckChasisNumber",
			"RNTT/TruckPermitNumber",
			"RNTT/TruckOwnerName",
			"RNTT/TruckColor",
			"RNTT/TruckCargoType",
			"RNTT/TruckEstado",
			"RNTT/TruckEstadoText",
			"RNTT/TruckEstadoReason",
			"RNTT/TruckRotulo",
			"RNTT/TruckInstitution",
			"RNTT/TruckCargoPolicy",
			"RNTT/TruckRfid",
			"RNTT/TruckCreatedDate",
			"RNTT/RawJson",
			"RNTT/LastUpdate",
			"RNTT/CommStatus",
		],
		[
			True,
			bool(driver) or bool(truck),
			authorized,
			"OK",
			str(get_any(driver, ["RNTT", "DriverRnttCode"], "")),
			get_any(driver, ["Nombre completo", "FullName", "DriverFullName"], driver_full_name(driver)),
			get_any(driver, ["Cedula", "DriverCedula", "NumeroCedula"], ""),
			get_any(driver, ["Licencia", "DriverLicense", "NumeroLicencia"], ""),
			get_any(driver, ["Tipo licencia", "DriverLicenseType", "TipoLicencia"], ""),
			get_any(driver, ["Expiracion licencia", "DriverLicenseExpiration", "ExpiracionLicencia"], ""),
			get_any(driver, ["Vencimiento afiliacion", "DriverAffiliationExpiration", "ENDDATE"], ""),
			get_any(driver, ["Rotulo asociado", "DriverRotulo", "Rotulo"], ""),
			get_any(driver, ["Empresa/Sindicato", "DriverCompany", "Empresa", "Sindicato"], ""),
			int(get_any(driver, ["Estado bruto", "DriverBdgsts", "bdgsts"], -1)),
			get_any(driver, ["Estado bruto texto", "DriverBdgstsText"], driver_bdgsts_text(driver)),
			driver_status,
			get_any(driver, ["Motivo interpretado", "DriverInterpretedReason"], driver_reason),
			get_any(truck, ["Placa/TruckName", "TruckName"], ""),
			get_any(truck, ["Chasis", "TruckChasisNumber"], ""),
			get_any(truck, ["Permiso", "TruckPermitNumber"], ""),
			get_any(truck, ["Propietario", "TruckOwnerName"], ""),
			get_any(truck, ["Color", "TruckColor"], ""),
			get_any(truck, ["Tipo carga", "TruckCargoType", "TipoCarga"], ""),
			int(get_any(truck, ["Estado", "TruckEstado"], -1)),
			truck_status,
			get_any(truck, ["Estado motivo", "TruckEstadoReason"], truck_reason),
			get_any(truck, ["Rotulo", "TruckRotulo"], ""),
			get_any(truck, ["Institution", "Institucion", "TruckInstitution"], ""),
			get_any(truck, ["Poliza carga", "TruckCargoPolicy", "PolizaCarga"], ""),
			get_any(truck, ["RFID", "TruckRfid"], ""),
			get_any(truck, ["Fecha creacion", "TruckCreatedDate", "FechaCreacion"], ""),
			system.util.jsonEncode(data),
			now_text(),
			"OK",
		],
	)

def ingest_rfid():
	data, status = read_json_file(FILES["RFID"])
	if status != "OK":
		write_tags(["RFID/CommStatus", "RFID/LastUpdate"], [status, now_text()])
		return

	epc = get_any(data, ["TagEpc", "tag_epc", "epc", "rfid"], "")
	read_time = get_any(data, ["ReadTimestamp", "read_timestamp", "timestamp"], now_text())

	write_tags(
		[
			"RFID/Trigger",
			"RFID/TagEpc",
			"RFID/TagTid",
			"RFID/ReaderIp",
			"RFID/ReaderName",
			"RFID/Antenna",
			"RFID/Rssi",
			"RFID/ReadCount",
			"RFID/ReadTimestamp",
			"RFID/VehicleMatched",
			"RFID/PlateExpected",
			"RFID/ValidFormat",
			"RFID/ReaderStatus",
			"RFID/RawJson",
			"RFID/LastUpdate",
			"RFID/CommStatus",
		],
		[
			True,
			epc,
			get_any(data, ["TagTid", "tag_tid", "tid"], ""),
			get_any(data, ["ReaderIp", "reader_ip"], ""),
			get_any(data, ["ReaderName", "reader_name"], "RFID Local POC"),
			int(get_any(data, ["Antenna", "antenna"], 1)),
			float(get_any(data, ["Rssi", "rssi"], 0.0)),
			int(get_any(data, ["ReadCount", "read_count"], 1)),
			read_time,
			bool(get_any(data, ["VehicleMatched", "vehicle_matched"], len(clean(epc)) > 0)),
			get_any(data, ["PlateExpected", "plate_expected"], ""),
			len(clean(epc)) > 0,
			get_any(data, ["ReaderStatus", "reader_status"], "OK"),
			system.util.jsonEncode(data),
			now_text(),
			"OK",
		],
	)

def ingest_navis():
	data, status = read_json_file(FILES["Navis"])
	if status != "OK":
		write_tags(["Navis/CommStatus", "Navis/LastUpdate"], [status, now_text()])
		return

	truck = get_nested(data, ["truck", "data"], None) or get_any(data, ["data"], {}) or {}
	driver = get_nested(data, ["driver", "data"], None) or {}

	write_tags(
		[
			"Navis/Trigger",
			"Navis/Found",
			"Navis/Status",
			"Navis/TruckId",
			"Navis/TruckLicense",
			"Navis/TruckLicenseState",
			"Navis/TruckLicenseExpirationDate",
			"Navis/InternalTruck",
			"Navis/LastTrkc",
			"Navis/LastTruckDriverName",
			"Navis/LifeCycleState",
			"Navis/DriverName",
			"Navis/DriverCardId",
			"Navis/DriverLicense",
			"Navis/RawJson",
			"Navis/LastUpdate",
			"Navis/CommStatus",
		],
		[
			True,
			bool(get_any(data, ["success"], True)),
			get_any(truck, ["status"], get_any(data, ["status"], "OK")),
			get_any(truck, ["id"], ""),
			get_any(truck, ["license"], ""),
			get_any(truck, ["license_state"], ""),
			get_any(truck, ["license_expiration_date"], ""),
			bool(get_any(truck, ["internal_truck"], False)),
			get_any(truck, ["last_trkc"], ""),
			get_any(truck, ["last_truck_driver_name"], ""),
			get_any(truck, ["life_cycle_state"], ""),
			get_any(driver, ["name"], ""),
			get_any(driver, ["card_id"], ""),
			get_any(driver, ["license"], ""),
			system.util.jsonEncode(data),
			now_text(),
			"OK",
		],
	)

def ingest_wialon():
	data, status = read_json_file(FILES["Wialon"])
	if status != "OK":
		write_tags(["Wialon/CommStatus", "Wialon/LastUpdate"], [status, now_text()])
		return

	unit = get_any(data, ["selected_unit"], {}) or data
	try:
		units = data.get("unidades", [])
		if unit is data and len(units) > 0:
			unit = units[0]
	except:
		pass

	write_tags(
		[
			"Wialon/UnitId",
			"Wialon/UnitName",
			"Wialon/Latitude",
			"Wialon/Longitude",
			"Wialon/SpeedKph",
			"Wialon/Course",
			"Wialon/Altitude",
			"Wialon/Satellites",
			"Wialon/LastGpsTime",
			"Wialon/Online",
			"Wialon/RawJson",
			"Wialon/LastUpdate",
			"Wialon/CommStatus",
		],
		[
			str(get_any(unit, ["UnitId", "unit_id", "id"], "")),
			get_any(unit, ["UnitName", "unit_name", "nombre", "name"], ""),
			float(get_any(unit, ["Latitude", "lat"], 0.0)),
			float(get_any(unit, ["Longitude", "lon"], 0.0)),
			float(get_any(unit, ["SpeedKph", "speed", "velocidad"], 0.0)),
			float(get_any(unit, ["Course", "course", "rumbo"], 0.0)),
			float(get_any(unit, ["Altitude", "altitude", "altitud"], 0.0)),
			int(get_any(unit, ["Satellites", "satellites", "satelites"], 0)),
			get_any(unit, ["LastGpsTime", "last_gps_time", "ultimo_reporte"], ""),
			bool(get_any(unit, ["Online", "online"], True)),
			system.util.jsonEncode(data),
			now_text(),
			"OK",
		],
	)

def ingest_lpr():
	data, status, event_file = read_oldest_lpr_event()
	if status != "OK":
		write_tags(["LPR/CommStatus", "LPR/LastUpdate"], [status, now_text()])
		return

	plate = get_any(data, ["plate", "Plate", "PlateNormalized"], "")
	rotulo = get_any(data, ["rotulo", "Rotulo"], "")
	confidence = float(get_any(data, ["confidence", "Confidence"], 0.0))
	plate_timestamp = parse_lpr_timestamp(get_any(
		data, ["plate_timestamp", "PlateTimestamp"], None
	))
	rotulo_timestamp = parse_lpr_timestamp(get_any(
		data, ["rotulo_timestamp", "RotuloTimestamp"], None
	))
	read_timestamp = parse_lpr_timestamp(get_any(
		data, ["timestamp", "ReadTimestamp"], None
	))
	plate_matched = bool(get_any(
		data,
		["plate_matched", "PlateMatched"],
		confidence >= 80.0 and len(str(plate)) > 0,
	))

	qualities = write_tags(
		[
			"LPR/Trigger",
			"LPR/Plate",
			"LPR/PlateNormalized",
			"LPR/Rotulo",
			"LPR/Confidence",
			"LPR/RotuloConfidence",
			"LPR/PlateTimestamp",
			"LPR/RotuloTimestamp",
			"LPR/EventType",
			"LPR/EventSequence",
			"LPR/CameraId",
			"LPR/CameraName",
			"LPR/CameraIp",
			"LPR/FramePath",
			"LPR/ClipPath",
			"LPR/ReadTimestamp",
			"LPR/PlateMatched",
			"LPR/RawJson",
			"LPR/LastUpdate",
			"LPR/CommStatus",
		],
		[
			bool(get_any(data, ["trigger", "Trigger"], True)),
			plate,
			str(plate).replace("-", "").replace(" ", "").upper(),
			rotulo,
			confidence,
			float(get_any(data, ["rotulo_confidence", "RotuloConfidence"], 0.0)),
			plate_timestamp,
			rotulo_timestamp,
			get_any(data, ["event_type", "EventType"], ""),
			int(get_any(data, ["event_sequence", "EventSequence"], 0)),
			get_any(data, ["camera_id", "CameraId"], ""),
			get_any(data, ["camera_name", "CameraName"], ""),
			get_any(data, ["camera_ip", "CameraIp"], ""),
			get_any(data, ["frame_path", "FramePath"], ""),
			get_any(data, ["clip_path", "ClipPath"], ""),
			read_timestamp,
			plate_matched,
			system.util.jsonEncode(data),
			now_text(),
			"OK",
		],
	)
	write_ok = True
	for quality in qualities:
		if not quality.isGood():
			write_ok = False
	if event_file is not None and write_ok:
		event_file.delete()

for ingest_name, ingest_function in [
	("BioStar", ingest_biostar),
	("RFID", ingest_rfid),
	("RNTT", ingest_rntt),
	("Navis", ingest_navis),
	("Wialon", ingest_wialon),
	("LPR", ingest_lpr),
]:
	try:
		ingest_function()
	except Exception as exc:
		system.util.getLogger("HGAC").error(
			"HGAC ingest %s error: %s" % (ingest_name, str(exc))
		)
