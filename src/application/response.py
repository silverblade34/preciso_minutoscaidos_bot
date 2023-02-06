import requests
from src.mongo.connect import ConnectionMongo
from pymongo import MongoClient
import json, datetime
class ResponseBot:
    def __init__(self):
        pass
    def responseMostrar(self):
        try:
            listaempresas = self.listarEmpresas()
            payloadrutinas = []
            for empresa in listaempresas:
                print("ACA EMPIEZA A ANALIZAR UNA EMPRESA: " + empresa['empresa'])
                respApi = self.consumirApiMinutos(empresa['token'], empresa['depot'])
                payloadempresa = self.analizarRutaEmpresa(respApi, empresa['ruc'])
                payloadrutinas = payloadrutinas + payloadempresa
            payloadenviar = self.validarRutinasMongo(payloadrutinas)
            resultenviar = self.insertarRutinasMongo(payloadenviar)
            respuesta = []
            for resp in resultenviar.inserted_ids:
                respuesta.append(resp)
            return respuesta
        except Exception as err:
            return err
        

    def consumirApiMinutos(self, token, depot):
        data = {}
        data['token'] = token
        data['depot'] = depot
        headers = {
            'Content-Type' : 'application/json'
        }
        result = requests.post("http://127.0.0.1:3222/api/v1/rides_per_route", data = json.dumps(data), headers= headers)
        resp = result.json()
        return resp
    
    def listarEmpresas(self):
        connect = ConnectionMongo()
        db = connect.con
        col = db["tbcliente"]
        docs = col.find({}, {'_id': False})
        resp = []
        for doc in docs:
            dicc = {}
            if doc['status'] == True:
                dicc['empresa'] = doc['empresa']
                dicc['token'] = doc['token']
                dicc['depot'] = doc['depot']
                dicc['ruc'] = doc['ruc']
                resp.append(dicc)
        return resp
    
    def analizarRutaEmpresa(self, respApi, ruc):
        payload = []
        if 'data' in respApi:
            dataRutas = respApi['data']
            for ruta in dataRutas:
                resp = self.analizarDetailsRuta(ruta['details'], ruta['route'], ruc)
                payload = payload + resp
            return payload
        else:
            return payload   
    
    def analizarDetailsRuta(self, details, route, ruc):
        listaRutinas = []
        fecha_actual = datetime.datetime.now().strftime("%d-%m-%Y")
        dateunix = datetime.datetime.strptime(fecha_actual, "%d-%m-%Y")
        fechaunix = int(dateunix.timestamp())
        datetimes = details[0]['datetimes']
        plates = details[0]['plates']
        stops = details[0]['stops']
        # for x in datetimes:
        x = 0
        while x < len(datetimes):
            rutina = {}
            rutina['ruta'] = route
            rutina['ruc'] = ruc
            rutina['rutina'] = datetimes[x]['datetime']
            rutina['placa'] = plates[x]['plate']
            rutina['fecha'] = fecha_actual
            rutina['fechaunix'] = fechaunix
            identificador = str(rutina['ruta']) + (rutina['rutina']) + str(rutina['placa']) + str(rutina['fechaunix'])
            rutina['identificador'] = identificador.replace(" ","")
            rutinaparadas = []
            for parada in stops:
                dateparada = {}
                dateparada['parada'] = parada['name']
                dateparada['horaejecutada'] = parada['hejecutada'][x]['hora']
                dateparada['horaplanificada'] = parada['hplanificada'][x]['hora']
                dateparada['min'] = parada['min'][x]['time']
                rutinaparadas.append(dateparada)
            rutina['rutinaparadas'] = rutinaparadas
            if stops[-1]['hejecutada'][x]['hora'] != "--:--":
                listaRutinas.append(rutina)
            x += 1
        return listaRutinas
    
    def insertarRutinasMongo(self, payload):
        connect = ConnectionMongo()
        db = connect.con
        col = db["report_minutosc"]
        results = col.insert_many(payload)
        return results
    
    def consultarRutinasMongo(self):
        rutinasmongo = []
        connect = ConnectionMongo()
        db = connect.con
        col = db["report_minutosc"]
        fecha_actual = datetime.datetime.now().strftime("%d-%m-%Y")
        results = col.find({'fecha' : fecha_actual }, {'_id': False})
        for result in results:
            rutinasmongo.append(result)
        return rutinasmongo
    
    def validarRutinasMongo(self, listpayload):
        rutinasmongo = self.consultarRutinasMongo()
        payloadLimpio = []
        for rutina in listpayload:
            unic = 0
            for rutinamongo in rutinasmongo:
                if rutina['identificador'] == rutinamongo['identificador']:
                    unic += 1
            if unic == 0:
                payloadLimpio.append(rutina)
        return payloadLimpio

        



