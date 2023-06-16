from flask import Flask

from mattressMapDef import MattressHeatMap

app = Flask(__name__)

@app.route('/')
def index():
    return 'Bed Sheet is live!!!'

@app.route('/bedMap')
def bedMap():
    bedSheet = MattressHeatMap()
    bedSheet.listenForInternet()
    cpuSNo = bedSheet.getserial()
    print('Serial No #'+cpuSNo)
    # bedSheet.prepareBed()
    return "Bed map imported"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)