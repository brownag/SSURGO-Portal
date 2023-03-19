const url = 'http://localhost:8083/SSURGOPortalUI'
const fileCheckUrl = 'http://localhost:8083/fileExists'
//Database Inventory Table Constants
const dbTableId = 'databaseTable'
const dbTableContainer = 'dbTableContainer'

//Name of columns and their onclick events
const dbTableHeaders = {
    'Area Symbol' : ["sortTable(1, 'databaseTableBody', true, 'text')", "Area Symbol of SSURGO in database"],
    'Area Name' : ["sortTable(2, 'databaseTableBody', true, 'text')", "Area Name of SSURGO in database"],
    'SSURGO Version Date' : ["sortTable(3, 'databaseTableBody',true, 'date')", "Version date for SSURGO data in database"],
    'Tabular Only' : ["sortTable(4, 'databaseTableBody', true, 'tabularOnly')", "Indicates that only tabular data exists for area symbol"]
}
//SSA Inventory Table Constants
const importTableId = 'importTable'
const importTableContainer = 'importTableContainer'

//Name of columns and their onclick events
const importTableHeaders = {
    'Folder Name' : [`sortTable(1, '${importTableId}',  true, 'text', 'tbody')`, "Name of folder containing SSURGO data"],
    'Area Symbol' : [`sortTable(2, '${importTableId}', true, 'text', 'tbody')`, "Area Symbol of SSURGO in the folder"],
    'Area Name' : [`sortTable(3, '${importTableId}', true, 'text', 'tbody')`, "Area Name of SSURGO in the folder"],
    'Folder SSURGO Version Date' : [`sortTable(4, '${importTableId}', true, 'date', 'tbody')`, "Version date of SSURGO data in folder"],
    'Exists in Database' : [`sortTable(5, '${importTableId}', true, 'versionCheck', 'tbody')`, "Indicates SSURGO area symbol in folder already exists in database"],
    'Database SSURGO Version Date' : [`sortTable(6, '${importTableId}', true, 'date', 'tbody')`, "Version date for SSURGO data in database"]
}
//Constants to determine which part of the page is being populated by the folder tree
    //If modified the html will also have to follow suit in places where correlated javascript methods are called I.E. executeFolderTreeRequest and initializeTreeView
const openDatabaseLocation = 'openDatabaseLocation'
const databaseTreeViewTableId = 'databaseTreeViewTable'
const importTreeViewTableId = 'importTreeViewTable'
const ssaFolderLocation = 'ssaFolderLocation'
//Name of columns and their onclick events
const databaseTreeViewHeaders = {
    'Name' : "doubleSort(0, 'databaseTreeViewTableFolderSection', 'databaseTreeViewTableFileSection', 'text')", 
    'Date modified' : "doubleSort(1, 'databaseTreeViewTableFolderSection', 'databaseTreeViewTableFileSection', 'date')", 
    'Type' : "sortTable(2, 'databaseTreeViewTableFileSection', false, 'text')", 
    'Size' : "sortTable(3, 'databaseTreeViewTableFileSection', false, 'fileSize')"}

const ssurgoTreeViewHeaders = {
    'Name' : "sortTable(0, 'importTreeViewTableFolderSection', false, 'text')", 
    'Date modified' : "sortTable(1, 'importTreeViewTableFolderSection', false, 'date')"
}
//Constants for requests going to Data Loader
const databaseTableRequest = 'getdatabaseinventory'
const createTemplateDatabaseRequest = 'createTemplateDatabase'
const copyTemplateFileRequest = 'copytemplatefile'
const deleteAreaSymbolRequest = 'deleteareasymbols'
const getFolderTreeRequest = 'getfoldertree'
const pretestImportCandidatesRequest = 'pretestimportcandidates'
const importCandidatesRequest = 'importcandidates'
const getTemplateCatalogRequest = 'gettemplatecatalog'

//Variables for paths
var databasePath
var folderPath
var databaseName
var requestLocation
var emptyTemplates // holds the emptyTemplates Object from the config.py file
//Variables for flags
var stopProgress = false
var rootPath
var overwriteChecked = false
var duplicateSSAs = {}
/**Main function for communicating with the server*/
async function sendData(data){
    //first we send the data for the server and wait
    let request = data.request
    let returnedResponse
    await fetch(url, {
        method : 'POST',
        headers: {'Content-Type' : 'application/json'},
        body: JSON.stringify(data)},
    ).catch(function(){
        $('#serverClosedModal').modal("show")
    })    
    //then we make sure the response is in JSON and make a JSON object
    .then(response =>response.json())
    //Then we handle the data
    .then(function(response){
        try{
            //This can probably be separated into a separate method
            if(request == databaseTableRequest){
                databaseTable.totalRows = Object.keys(response.records).length
                databaseTable.data = response.records
                setDatabaseName(databasePath)
                buildDatabaseTable()
                document.getElementById('emptyDatabaseGrayIcon').setAttribute('style', 'display: none')
            }
            else if(request == pretestImportCandidatesRequest){
                getTotalFolders(response.subfolders)
                setErrorToggleDisplay()
                importTable.data = response.subfolders
                buildImportTable()
                setFolderName(folderPath)
                if(importTable.errorFolders > 0){
                    document.getElementById('toggleErrorDiv').removeAttribute('style')
                }
                else{
                    document.getElementById('toggleErrorDiv').setAttribute('style', 'display: none')
                }
                if(Object.keys(duplicateSSAs).length > 0){
                    document.getElementById('toggleDuplicateDiv').removeAttribute('style')
                }
                else{
                    document.getElementById('toggleDuplicateDiv').setAttribute('style', 'display: none')
                }
                setDuplicateToggleDisplay()
            }
            else if(request == createTemplateDatabaseRequest){
                databasePath = response.path
            }
            else if(request == copyTemplateFileRequest){
                returnedResponse = response
            }
            else if(request == importCandidatesRequest){
                returnedResponse = response
            }
            else if(request == deleteAreaSymbolRequest){
                returnedResponse = response
            }
            else if (request == getTemplateCatalogRequest){
                emptyTemplates = response.emptytemplates
            }
            else if (request == getFolderTreeRequest){
                if(requestLocation == databaseTreeViewTableId){
                    //Builds out the tree view for selecting a database
                    let search = document.getElementById("databaseSearchText")
                    search.setAttribute('onchange', `executeFolderTreeRequest('${databaseTreeViewTable.tableId}', "${rootPath}", true, updatedValue('databaseSearchText'))`)
                    databaseTreeViewTable.data = response.nodes
                    databaseTreeViewTable.populateTreeViewTable()
                }
                else if(requestLocation == importTreeViewTableId){
                    //Builds out the tree view to select an SSA parent folder
                    let search = document.getElementById("ssaSearchTextbox") //Set the id of the search bar.
                    search.setAttribute('onchange', `executeFolderTreeRequest('${importTreeViewTable.tableId}', "${rootPath}", false, updatedValue('ssaSearchTextbox'))`)
                    importTreeViewTable.data = response.nodes
                    importTreeViewTable.populateTreeViewTable()
                    document.getElementById('selectSsurgoFolderFinalizeBtn').setAttribute('onclick', `selectSSAParentFolder("${rootPath}")`)
                }
            }
            else if (request = 'getstatus'){
                echo(response)
            }
            else(
                console.log("Unknown request: " + response.request.request)
            )
        }
        catch(error){
            logJavaScriptError(error.stack)
        }
        // Need to implement logic here to dictate if a dbtable is being created or a folder table is being created
        //buildTable(data.databaseItems, 'databaseTable')
    })//TODO: This would be a great place to implement error handling and present a message to the users
    //If we are expecting to return an item, return it.
    if(returnedResponse != null){
        return(returnedResponse)
    }
}

/**Send JavaScript errors to the data loader to place in the log file.*/
function logJavaScriptError(eventStack){
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type' : 'application/json'},
        body: JSON.stringify({
            'request': 'logjavascripterror',
            'eventStack': eventStack
        })
    })
}

/************************************************************Table Functions**********************************/
class Table {
    constructor(tableId, headers, data, tableContainer){
        this.tableId = tableId
        this.headers = headers
        this.data = data        
        this.tableContainer = document.getElementById(tableContainer)
        this.thead = document.createElement('thead')
    }
    
    /**Builds the container for the table */
    buildTable(){
        let tableExists = document.getElementById(this.tableId)
        if(tableExists){
            document.getElementById(this.tableId).remove()
        }
        this.table = document.createElement('table')
        this.table.setAttribute('id', this.tableId)
        this.table.setAttribute('class', 'table table-hover')
        this.tableContainer.appendChild(this.table)
    }

    /**Builds the table header for the table */
    buildTableHeader(){
        this.table.appendChild(this.thead)
        this.thead.innerHTML = ""
        let row = document.createElement('tr')
        this.thead.appendChild(row)
        for(let head in this.headers){
            let col = document.createElement('th')
            row.appendChild(col)
            let colText = document.createTextNode(head)
            col.appendChild(colText)
            col.setAttribute("onclick", this.headers[head])
            addButtonFunctionality(col)
            col.setAttribute("role", "columnheader")
            col.setAttribute("scope", "col")
            let img = document.createElement('img')
            img.setAttribute("alt", "")
            img.setAttribute('src', '/static/images/sorting-icon.svg')
            col.appendChild(img)
        }
    }
}

class CheckboxTable extends Table {
    constructor(tableId, headers, data, tableContainer, selectAllId, selectAllLabel, actionButton, checkboxId, checkboxClass, counterId){
        //tableId must match the name of the class object that will be created.
            // I.E. let importTable = {tableId = importTable}
        super(tableId, headers, data, tableContainer)
        this.selectAllId = selectAllId
        this.selectAllLabel = selectAllLabel
        this.actionButton = actionButton
        this.checkboxId = checkboxId
        this.checkboxClass = checkboxClass
        this.counterId = counterId
        this.totalRows = 0
        this.selectedCheckboxes = []
    }

    buildCheckboxTableHeader(targetTbody = false){
        this.table.appendChild(this.thead)
        this.thead.innerHTML = ""
        let row = document.createElement('tr')
        this.thead.appendChild(row)
        let selectColumn = document.createElement('th')
        row.appendChild(selectColumn)
        let selectColumnItem = document.createElement('input')
        selectColumnItem.setAttribute('type', 'checkbox')
        selectColumn.appendChild(selectColumnItem)
        selectColumnItem.setAttribute('id', this.selectAllId)
        selectColumnItem.setAttribute('aria-label', this.selectAllLabel)        
        selectColumn.setAttribute("aria-label", "Select all rows")
        selectColumnItem.setAttribute('title', this.selectAllLabel)
        selectColumnItem.setAttribute('onchange', `${this.tableId}.selectDeselectAll(${targetTbody})`)
        addEnterEventListener(selectColumnItem)
        for(let head in this.headers){
            let col = document.createElement('th')
            col.setAttribute("scope", "col")
            row.appendChild(col)
            let colText = document.createTextNode(head)
            col.appendChild(colText)
            col.setAttribute("onclick", this.headers[head][0])
            if(this.headers[head][1] != ""){
                col.setAttribute("title", this.headers[head][1])
            }
            addButtonFunctionality(col)
            col.setAttribute("role", "columnheader")
            let img = document.createElement('img')
            img.setAttribute('alt', '')
            img.setAttribute('src', '/static/images/sorting-icon.svg')
            col.appendChild(img)
        }
    }

    /**Sets the attributes of select checkboxes. Must be called within a for loop. Returns row.*/
    setSelectCheckbox(appendToTable, tableBody, checkboxName, targetTbody = false){
        let row = document.createElement('tr')
        let col = document.createElement('th')
        this.table.appendChild(tableBody)
        let checkbox = document.createElement('input')
        checkbox.setAttribute('type', 'checkbox')
        checkbox.setAttribute('onchange', `${this.tableId}.getSelectedCheckboxes(${targetTbody})`)
        checkbox.setAttribute('class', this.checkboxClass)
        addEnterEventListener(checkbox)
        checkbox.setAttribute('id', this.checkboxId + checkboxName)
        checkbox.setAttribute('aria-label', this.checkboxId + checkboxName)
        if(appendToTable){
            tableBody.appendChild(row);
            row.appendChild(col)
            col.appendChild(checkbox)
            // If Tabular only checkbox is selected, prechecks get reexecuted & the table is repainted.
            // In order to keep the UI updated with the rows that were selected, we have to re-check the
            // checkboxes and reapply the styling.
            if (importTable.selectedCheckboxes != null && importTable.selectedCheckboxes.includes(rowData.childfoldername))
            {
                checkbox.setAttribute('checked', 'true')
                checkbox.parentNode.parentNode.parentNode.setAttribute('style', 'background: #D4E2F2; border-bottom-color: #6c757d;')
            }
            return row
        }
    }

    /**Return list of selected checkbox, then create JSON object to return to server. */
    getSelectedCheckboxes(targetTbody = false){
        let table = document.getElementById(this.tableId)
        let checkBoxes = table.getElementsByClassName(this.checkboxClass)
        this.selectedCheckboxes = []
        for(var i = 0; i < checkBoxes.length; i++){
            if(checkBoxes[i].checked){
                let selectedName = checkBoxes[i].id
                this.selectedCheckboxes.push(selectedName.replace(this.checkboxId, ''))
                if(targetTbody){
                    checkBoxes[i].parentNode.parentNode.parentNode.setAttribute('style', 'background: #D4E2F2; border-bottom-color: #6c757d;')
                }
                else{
                    checkBoxes[i].parentNode.parentNode.setAttribute('style', 'background: #D4E2F2; border-bottom-color: #6c757d;')
                }
            }
            else{
                if(targetTbody){
                    checkBoxes[i].parentNode.parentNode.parentNode.setAttribute('style', 'border-bottom-color: #dee2e6;')
                }
                else{
                    checkBoxes[i].parentNode.parentNode.setAttribute('style', 'border-bottom-color: #dee2e6;')
                }
            }
            document.getElementById(this.counterId).innerHTML = `${this.selectedCheckboxes.length} out of ${this.totalRows} selected`
            if(this.selectedCheckboxes < 1){
                this.actionButton.disabled = true
            }
            else{
                this.actionButton.disabled = false
            }
        }
    }

    selectDeselectAll(targetTbody = false){
        let master = document.getElementById(this.selectAllId)
        let checkboxes = document.getElementsByClassName(this.checkboxClass)
        if(master.checked){
            for(var i=0; i<checkboxes.length; i++){
                if(checkboxes[i].type=='checkbox'){
                    checkboxes[i].checked=true;
                }
            }
        }
        else{
            for(var i=0; i<checkboxes.length; i++){
                if(checkboxes[i].type=='checkbox'){
                    checkboxes[i].checked=false
                }
            }
        }
        this.getSelectedCheckboxes(targetTbody)
    }
}

class TreeViewTable extends Table {
    constructor(tableId, headers, data, tableContainer, editablePathId, clickablePathId, showFiles){
        super(tableId, headers, data, tableContainer)
        this.editablePathId = editablePathId
        this.clickablePathId = clickablePathId
        this.showFiles = showFiles
    }

    populatePathNavigation(){
        let root = rootPath
        root = root.replaceAll('//', '/')
        root = root.replaceAll('/', '\\')
        var parentFolder = root.split('\\')
        //If the folder is empty or is only a \ then remove it from the list
        for(let folder in parentFolder){
            if(parentFolder[folder] == "" || parentFolder[folder] == '\\' || parentFolder[folder] == '/'){
                parentFolder.pop(folder)
            }
        }
        var separateParentFolders = parentFolder
        parentFolder = parentFolder.join('/')
        this.createClickablePath(separateParentFolders)
        this.populateEditablePath()
    }

    createClickablePath(folders){
        var folderPath = []
        let clickablePathContanier = document.getElementById(this.clickablePathId)
        clickablePathContanier.innerHTML = ""
        //Builds out the clickable items to navigate the folders
        //else
        for(let folder in folders){
            if(folders[folder] != ""){
                let folderPathTemp
                let image = document.createElement('img')
                image.setAttribute('src', '/static/images/rightCaret.svg')
                image.setAttribute('alt', '/')
                let rootSelectSpan = document.createElement('p')
                let folderName = folders[folder]
                rootSelectSpan.setAttribute('value', folderName)
                addButtonFunctionality(rootSelectSpan)
                let textNodeContainer = document.createElement('span')
                let textNode = document.createTextNode(folderName)
                rootSelectSpan.setAttribute('class', 'folderName')
                textNodeContainer.appendChild(textNode)
                rootSelectSpan.appendChild(textNodeContainer)
                rootSelectSpan.appendChild(image)
                folderPath += folders[folder] + '/'
                if(folderPath.length > 3 && folderPath.substr(-1) == "/"){
                    folderPathTemp = folderPath.substr(0, folderPath.length -1)
                }
                else{
                    folderPathTemp = folderPath
                }
                rootSelectSpan.setAttribute('onclick', `executeFolderTreeRequest("${this.tableId}", "${folderPathTemp}", ${this.showFiles})`)                
                clickablePathContanier.appendChild(rootSelectSpan)
            }
        }
    }

    populateEditablePath(){
        let rootTextbox  = document.getElementById(this.editablePathId)
        rootTextbox.innerHTML = rootPath
        rootTextbox.value = rootPath
    }
    
    populateTreeViewTable(){
        this.populatePathNavigation()
        this.buildTable()
        this.buildTableHeader()
        this.table.setAttribute('class', 'table table-hover')
        this.folderSection = document.createElement('tbody')
        this.folderSection.setAttribute('id', `${this.tableId}FolderSection`)
        this.fileSection = document.createElement('tbody')
        this.fileSection.setAttribute('id', `${this.tableId}FileSection`)
        for(let row in this.data){
            let tr = document.createElement('tr')
            if(this.data[row].type != "File Folder" && !this.showFiles ){
                continue
            }
            row = this.data[row]
            for(let column in row){
                let td
                if(column == "name"){
                    td = document.createElement("th")
                    td.setAttribute("rowgroup", "1")
                    td.setAttribute("scope", "rowgroup")
                }
                else{
                    td = document.createElement('td')
                }
                td.innerHTML = row[column]
                if((column != "type" && column != "size" && this.showFiles == false) || this.showFiles == true){                    
                    tr.appendChild(td)
                }
            }
            if(row.type == "File Folder"){
                tr.setAttribute('onclick', `executeFolderTreeRequest("${this.tableId}", "${rootPath}/${row.name}", ${this.showFiles})`)                
                let img = document.createElement("img")
                img.setAttribute("src", "/static/images/folderIcon.svg")
                img.setAttribute("class", "treeViewFolderIcon")
                img.setAttribute("alt", "")
                let folderNameTd = tr.getElementsByTagName("th")[0]
                folderNameTd.prepend(img)  
                this.folderSection.appendChild(tr)
            }
            else{
                if(row.type.toLowerCase() == "gpkg file" || row.type.toLowerCase() == "sqlite file"){
                    let fileExtension = row.type.toLowerCase().split(" ")[0]
                    tr.setAttribute('onclick', `selectDatabase( "${rootPath}", "${rootPath}/${row.name}.${fileExtension}")`)
                    let img = document.createElement("img")
                    img.setAttribute("src", "/static/images/emptyDatabaseIcon.svg")
                    img.setAttribute("class", "treeViewDatabaseIcon")
                    img.setAttribute("alt", "")
                    let fileNameTd = tr.getElementsByTagName("th")[0]
                    fileNameTd.prepend(img) 
                    this.fileSection.appendChild(tr)
                }
            }
        }
        this.table.appendChild(this.folderSection)
        this.table.appendChild(this.fileSection)
    }
}
/*******************************************TREE VIEW METHODS*********************************************** */
let databaseTreeViewTable = new TreeViewTable(
    tableId = databaseTreeViewTableId,
    headers = databaseTreeViewHeaders,
    data = [],
    tableContainer = "databaseTreeViewTableContainer",
    editablePathId = "databaseTextBox",
    clickablePathId = "clickablePathContainer",
    showFiles = true
)

let importTreeViewTable = new TreeViewTable(
    tableId = importTreeViewTableId,
    headers = ssurgoTreeViewHeaders,
    data = [],
    tableContainer = "importTreeViewTableContainer",
    editablePathId = "ssaTextBox",    
    clicakblePathId = "ssaClickablePathContainer",
    showFiles = false
)

/**Check if cookie exists, otherwise set default value. Then send request to the python server.*/
async function initializeTreeView(request, cookie){
    if(cookieExists(cookie)){
        path = getCookie(cookie)
    }
    else{
        path = 'C:/'
    }
    requestLocation = request
    rootPath = path.replaceAll('\\', '/')
    rootPath = rootPath.replaceAll ('//', '/')
    let data = {'request': getFolderTreeRequest, 'path': rootPath, 'folderpattern' : "", 'ignorefoldercase': true,
        'filepattern' : "", 'ignorefilecase': true, 'showfiles': true, 'maxdepth': 0}
    await sendData(data)
}

/**Sends "getfoldertree" request to the server*/
async function executeFolderTreeRequest(request, path, showfiles, folderPattern = ""){
    requestLocation = request
    rootPath = path.replaceAll('\\', '/')
    let data = {'request': getFolderTreeRequest, 'path': rootPath, 'folderpattern' : `.*${folderPattern}.*`, 'ignorefoldercase': true,
        'filepattern' : `.*${folderPattern}.*`, 'ignorefilecase': true, 'showfiles': showfiles, 'maxdepth': 0}
await sendData(data)
}

/**Gets the updated value of a element. {I.E. user types in a textbox}*/
function updatedValue(elementId){
    val = document.getElementById(elementId).value
    return val
}

async function selectDatabase(cookieRoot,  path){
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //close the help menu if it was open before navigating away
    document.getElementById("importNavLink").click() //Navigate back to the Import table
    document.getElementById("deleteBtn").disabled = true //disable the delete button after selecting a database
    //always reset the deleteCheckboxesSelected[] array
    deleteCheckboxesSelected = []
    setCookie(databaseTableRequest, cookieRoot, 365)
    databasePath = path
    let data = {'request' : databaseTableRequest, 'database' : databasePath, 'wheretext' : ""}
    await sendData(data)
    if (folderPath != null) {
        selectSSAParentFolder(folderPath)
    }
}

/**Set Import Folder cookie, then send request to server to pretest subfolders */
async function selectSSAParentFolder(path, resetCheckboxes = true){      
    document.getElementById("importNavLink").click() //Default back to the Import table
    //always reset the importTable.selectedCheckboxes[] array
    if (resetCheckboxes) {
        importTable.selectedCheckboxes = []
    }
    //define elements
    let errorDiv = document.getElementById('errorDiv')
    let loadScreen = document.getElementById('folderLoadingScreen')
    let table = document.getElementById(importTableId)
    let tableFooter = document.getElementById('folderRecordCounter')
    let errorDivBtn = document.getElementById('toggleErrorDiv')
    let duplicateDiv = document.getElementById('duplicateDiv')
    let duplicateDivBtn = document.getElementById('toggleDuplicateDiv')
    //disable buttons while loading
    Array.from(document.getElementsByClassName('toggleDisableOnLoad')).forEach(element => element.disabled = true)
    Array.from(document.getElementsByClassName('nav-link')).forEach(element => element.disabled = false)
    document.getElementById('databaseUploadGrayIcon').setAttribute('style', 'display: none')
    //If table exists, hide
    if(typeof(table) != 'undefined' && table != null){
        table.setAttribute('style', 'display:none;')
        tableFooter.setAttribute('style', 'display:none;')
    }
    loadScreen.removeAttribute('style')
    errorDivBtn.setAttribute('style', 'display:none;')
    duplicateDivBtn.setAttribute('style', 'display:none;')
    errorDiv.innerHTML = ''
    duplicateDiv.innerHTML = ''
    setCookie(pretestImportCandidatesRequest, path, 365)
    folderPath = path
    isTabularOnly = document.getElementById("loadTabularData").checked
    let data = {'request' : pretestImportCandidatesRequest, 'database' : databasePath, 'root' : folderPath, 'istabularonly': isTabularOnly}
    await sendData(data)
    //Display table and hide loading message
    table = document.getElementById(importTableId) //redefine table. This is necessary if the table did not exist before sendData.
    tableFooter = document.getElementById("folderRecordCounter")
    loadScreen.setAttribute('style', 'display:none;')
    table.removeAttribute('style')
    tableFooter.removeAttribute('style')
    //re-enable buttons after pretests are complete
    Array.from(document.getElementsByClassName('toggleDisableOnLoad')).forEach(element => element.disabled = false)
    if(databaseTable.selectedCheckboxes.length == 0){
        document.getElementById("deleteBtn").disabled = true
    }
    if (importTable.selectedCheckboxes.length <= 0) {
        document.getElementById("importBtn").disabled = true
    }
    //check if the 'SSURGO Data in Database' tab is "active"
    let ssurgoDataInDatabaseTab = document.getElementById("databaseNavLink");
    if (ssurgoDataInDatabaseTab.classList.contains("active")) {
        document.getElementById("refreshBtn").setAttribute("style", "display: none")
    } else {
        document.getElementById("refreshBtn").setAttribute("style", "display: block")
    }
}

//re-execute pre-tests when the "Load Tabular Data Only" button is clicked
$("#loadTabularData").click(function(){
    selectSSAParentFolder(folderPath, false)
})

//re-execute pre-tests when the "Refresh" button is clicked
$("#refreshBtn").click(function(){
    selectSSAParentFolder(folderPath, false)
})

//Remove the "Refresh" button from displaying when the SSURGO Data In Database Tab is clicked
$("#databaseNavLink").click(function(){
    document.getElementById("refreshBtn").setAttribute("style", "display: none")
})

//Display the "Refresh" button next to the Import SSURGO Data Tab when it's clicked AND the folderPath (SSURGO Data folder) has been set
$("#importNavLink").click(function(){
    if(folderPath) {
        document.getElementById("refreshBtn").setAttribute("style", "display: block")
    }
})

/**Set cookie for selcted node and send data to the server. This is the method that executes when a user selects a child node*/
async function selectNode(request, cookieRoot, path){
    setCookie(request, cookieRoot, 365)
    let data = {'request' : request, 'database' : databasePath, 'path': path, 'istabularonly' : "", 'subfolders' : ""}
    await sendData(data)
}
/************************************************************END TREE VIEW METHODS ********************************* */

let importTable = new CheckboxTable(
    tableId = importTableId,
    headers = importTableHeaders,
    data = [],
    tableContainer = importTableContainer,
    selectAllId = 'selectDeselectAllSSA',
    selectAllLabel = 'Select Folder',
    actionButton = document.getElementById('importBtn'),
    checkboxId = 'importCheckbox',
    checkboxClass = 'folderCheckbox customCheckbox',
    counterId = 'folderRecordCounter',
    selectedCheckboxes = [],
);

let databaseTable = new CheckboxTable(
    tableId = dbTableId,
    headers = dbTableHeaders,
    data = [],
    tableContainer = dbTableContainer,
    selectAllId = 'selectDeselectAllDatabase',
    selectAllLabel = 'Select Database Inventory',
    actionButton = document.getElementById('deleteBtn'),
    checkboxId = 'deleteCheckbox',
    checkboxClass = 'dataCheckbox customCheckbox',
    counterId = 'databaseRecordCounter',
    selectedCheckboxes = [],
)


function buildDatabaseTable(){
    data = databaseTable.data
    databaseTable.buildTable()
    document.getElementById("databaseRecordCounter").innerHTML = `${databaseTable.selectedCheckboxes.length} out of ${databaseTable.totalRows} selected`
    databaseTable.buildCheckboxTableHeader()
    let tableBody = document.createElement('tbody')
    tableBody.setAttribute('id', 'databaseTableBody')
    let table = document.getElementById(databaseTable.tableId)
    table.appendChild(tableBody)
    for(subData in data){
        rowData = data[subData]
        let row = databaseTable.setSelectCheckbox(true, tableBody, subData)
        row.setAttribute("rowspan", "1")
        row.setAttribute("scope", "rowgroup")
        tableBody.appendChild(row)
        col = document.createElement('th')
        col.setAttribute("scope", "row")
        row.appendChild(col)
        let colText = document.createTextNode(subData)
        col.appendChild(colText)
        for(cell in rowData){
            let cellValue = rowData[cell]
            col = document.createElement('td')
            row.appendChild(col)
            if(cell == "saverest"){
                cellValue = formatDate(cellValue)
            }
            colText = document.createTextNode(cellValue)
            if(cell != 'istabularonly'){
                col.appendChild(colText)
            }
            //Add checkmark if SSA is tabular only
            else if(cell == "istabularonly" && rowData[cell] != false){
                let img = document.createElement("img")
                img.setAttribute("aria-label", "is tabular only")
                img.setAttribute("src", "/static/images/checkmarkFillBlue.svg")
                col.appendChild(img)
                col.setAttribute('value', 'true')
            }
            else if(cell == "istabularonly" && rowData[cell] == false){
                col.setAttribute('value', 'false')
            }
        }
    }
}

function buildImportTable(){
    let data = importTable.data
    importTable.buildTable()
    document.getElementById(importTable.tableId).classList.remove("table-hover")
    if(folderPath == null){
        document.getElementById("importAdvancedOptionsBtn").disabled = true
    }
    else{
        document.getElementById("importAdvancedOptionsBtn").disabled = false
    }
    importTable.buildCheckboxTableHeader(true)
    duplicateSSAs = {}
    for(subData in data){
        let tableBody = document.createElement('tbody')
        rowData = data[subData]
        if(rowData.preteststatus){
            let row = importTable.setSelectCheckbox(rowData.preteststatus, tableBody, rowData.childfoldername, true)
            row.firstChild.setAttribute("rowspan", Object.keys(data[subData].areasymbols).length)
            row.firstChild.setAttribute("scope", "rowgroup")
            tableBody.setAttribute("id", rowData.childfoldername)
            //For each value within rowData
            for(cell in rowData){
                if(cell == "childfoldername"){
                    cellValue = rowData[cell]
                    col = document.createElement('th')
                    col.setAttribute("rowspan", Object.keys(data[subData].areasymbols).length)
                    col.setAttribute("scope", "rowgroup")
                    colText = document.createTextNode(cellValue)
                    displayDuplicateSSA(rowData, col)
                    saveDuplicateSSA(rowData)
                    col.appendChild(colText)
                    row.appendChild(col)
                }
                /*Logic to build out subsections of the table. This will place each folder and the associated areas within the folder in its own tbody.*/
                else if(cell == "areasymbols"){
                    currentAreas = 0
                    for(area in rowData.areasymbols){
                        cellValue = area
                        col = document.createElement('td')
                        //If a folder has more than 1 associated areas, place two empty td's to format table correctly.
                        if(currentAreas > 0){
                            row = document.createElement('tr')
                            tableBody.appendChild(row)
                        }
                        colText = document.createTextNode(cellValue)
                        col.appendChild(colText)
                        row.appendChild(col)
                        //For each attribute within the areasymbol build out the table row
                        for(value in rowData.areasymbols[area]){
                            cellValue = rowData.areasymbols[area][value]
                            if((value =="dbversion" || value == "fileversion") && cellValue !=""){
                                cellValue = formatDate(cellValue)
                            }
                            col = document.createElement('td')
                            colText = document.createTextNode(cellValue)
                            col.appendChild(colText)
                            row.appendChild(col)
                            //Logic to populate the Exists in database column
                            if(value =="fileversion"){
                                let inDatabaseCol = document.createElement('td')               
                                row.appendChild(inDatabaseCol)
                                //Value does not exist in the database
                                if(rowData.areasymbols[area]["dbversion"] == ""){
                                    //Set value for sorting and 508 reasons
                                    inDatabaseCol.setAttribute("value", "Not in Database")
                                    continue
                                }
                                let img = document.createElement('img') 
                                inDatabaseCol.appendChild(img)
                                //Database verson and Folder version match
                                if(rowData.areasymbols[area]["fileversion"] == rowData.areasymbols[area]["dbversion"]){
                                    img.setAttribute("src", "/static/images/checkmarkFillGreen.svg")
                                    img.setAttribute("alt", "Versions match icon")
                                    inDatabaseCol.setAttribute("title", "SSURGO folder version date matches the SSURGO database version date.")
                                    inDatabaseCol.setAttribute("value", "Versions match")
                                }
                                //Database version and Folder verion do NOT match
                                else{
                                    img.setAttribute("src", "/static/images/warningIcon.svg")
                                    img.setAttribute("alt", "Versions do not match icon")
                                    inDatabaseCol.setAttribute("value", "Versions do not match")
                                    inDatabaseCol.setAttribute("title", "SSURGO folder version date does NOT match the SSURGO database version date.")
                                }
                            }
                        }
                        currentAreas++
                    }
                }
            }
        tableBody.appendChild(row)
        }
        else{
            populateErrorMessage(rowData, true)
            // If checkboxes were previously selected, but no longer pass the pre-test, we need to remove them
            // from the importTable.selectedCheckboxes Array. This only applies to the Import SSURGO Data Table.
            if (importTable.selectedCheckboxes != null && importTable.selectedCheckboxes.includes(rowData.childfoldername)) {
                let index = importTable.selectedCheckboxes.indexOf(rowData.childfoldername)
                importTable.selectedCheckboxes.splice(index, 1)
            }
        }
    }
    document.getElementById("folderRecordCounter").innerHTML = `${importTable.selectedCheckboxes.length} out of ${importTable.totalRows} selected`
    populateDuplicateMessage()
}

/**Adds info icon to columns sharing duplicate area symbols */
function displayDuplicateSSA(folderResponse, column){
    if("sharedSSAs" in folderResponse){
        //Adding an icon to the table row
        img = document.createElement("img")
        img.setAttribute("src", "/static/images/infoIcon.svg")
        img.setAttribute("alt", "duplicate areasymbol warning ")
        img.setAttribute("title", "This folder shares common area symbol(s) with another folder(s)")
        img.setAttribute("class", "infoIcon")
        column.appendChild(img)
    }
}

/**Saves the duplicate area symbols into an accessable variable */
function saveDuplicateSSA(folderResponse){
    if("sharedSSAs" in folderResponse ){
        for(ssa in folderResponse.sharedSSAs){
                if(!(ssa in duplicateSSAs)){
                    duplicateSSAs[ssa] = [folderResponse.childfoldername]
                }
                else{
                    duplicateSSAs[ssa].push(folderResponse.childfoldername)
                }
        }
    }
}

/**Creates duplicate area message */
function populateDuplicateMessage(){
    for(ssa in duplicateSSAs){
        let img = document.createElement('img')
        let div = document.createElement('div')
        let p = document.createElement('p')
        duplicateDiv = document.getElementById('duplicateDiv')
        img.setAttribute('src', 'static/images/infoIcon.svg')
        img.setAttribute('alt', 'info image icon')
        p.innerHTML = (`${ssa} is found in the following folders: ${duplicateSSAs[ssa].join(', ') }`)
        //Append children
        div.appendChild(img)
        div.appendChild(p)
        duplicateDiv.appendChild(div)
    }
}

/**Set the value for the total folder counters */
function getTotalFolders(folders){
    importTable.errorFolders = 0
    importTable.totalRows = 0
    for(item in folders){
        if(folders[item].preteststatus){
            importTable.totalRows += 1
        }
        else{
            importTable.errorFolders += 1
        }
    }
}

/**Resets the pretest error collapse button */
function setErrorToggleDisplay(){
    let errorDiv = document.getElementById('toggleErrorDiv')
    //Prevent duplication while keeping the img
    if(errorDiv.lastChild.tagName == 'P'){
        errorDiv.lastElementChild.remove()
    }
    let p = document.createElement('p')
    p.innerHTML = `${importTable.errorFolders} folders have errors. Files inside these folders do not match the structure needed to import. Click this message to view.`
    errorDiv.appendChild(p)
}

function setDuplicateToggleDisplay(){
    let duplicateDiv = document.getElementById('toggleDuplicateDiv')
    if(duplicateDiv.lastChild.tagName == "P"){
        duplicateDiv.lastElementChild.remove()
    }
    let p = document.createElement('p')
    p.innerHTML = `${Object.keys(duplicateSSAs).length} area symbol(s) are found in multiple folders. Click this message to view.`
    duplicateDiv.appendChild(p)
}

/**Creates the error message for folders that fail pretest */
function populateErrorMessage(rowData, isPretest){
    let img = document.createElement('img')
    let div = document.createElement('div')
    let p = document.createElement('p')
    let errorMessage = rowData["errormessage"].replaceAll("/", "\\")
    if(isPretest){
        errorDiv = document.getElementById('errorDiv')
        p.innerHTML = (`${rowData["childfoldername"]}: <b>Error Message:</b> ${errorMessage}`)
        img.setAttribute('src', 'static/images/warningIcon.svg')
        img.setAttribute('alt', 'warning image icon')
    }
    else{
        errorDiv = document.getElementById("progressErrorDiv")
        p.innerHTML = `${rowData["areaname"]} <b>Error Message:</b> ${errorMessage}}`
        img.setAttribute("src", "static/images/failedIcon.svg")
        img.setAttribute("alt", "failed image icon")
    }

    //Append children
    div.appendChild(img)
    div.appendChild(p)
    errorDiv.appendChild(div)
    //button will be implemented at a later time
    /*
        let btn = document.createElement('button')
        btn.setAttribute('class', 'errorButton')
        btn.setAttribute('id', `errorButton${rowData['childfoldername']}`)
        btn.innerHTML = "How to fix the problem?"
        div.appendChild(btn)
    */
}

/*******************************Sort Logic******************************************/

function sortDateLogic(xDate, yDate, isAscending){
    let xdate = new Date(Date.parse(xDate))
    let ydate = new Date(Date.parse(yDate))
    if(isAscending){
        if((!dateIsValid(xdate) && dateIsValid(ydate)) || (xdate > ydate)){
            return true
        }
        else{
            return false
        }
    }
    else{
        if((dateIsValid(xdate) && !dateIsValid(ydate)) || (xdate < ydate)){
            return true
        }
        else{
            return false
        }
    }
}

function dateIsValid(date){
    return date instanceof Date && !isNaN(date)
}

function doubleSort(n, target1, target2, sortLogic){
    sortTable(n, target1, false, sortLogic)
    sortTable(n, target2, false, sortLogic)
}

// JavaScript program to illustrate
// Table sort for both columns and both directions.
function sortTable(n, target, isCheckboxTable, typeOfSort, recordRowType = "tr" ) {
    let tableBody;
    tableBody = document.getElementById(target);
    let i, x, y, count = 0;
    let switching = true;
    let table = document.querySelector(`#${tableBody.getAttribute("id")}`).parentElement
    // Order is set as ascending
    let direction = "ascending";
    if(recordRowType == "tr"){
        var sortImages = document.querySelectorAll(`#${table.getAttribute("id")} >thead>tr>th>img`)
    }
    else{
        var sortImages = document.querySelectorAll(`#${table.getAttribute("id")} table>thead>tr>th>img`)
    }
    
    let selectedSortImages = document.querySelector(`#${table.getAttribute("id")} th:nth-of-type(${n + 1})>img`)
    for(img of sortImages){
        img.setAttribute("src", "static/images/sorting-icon.svg")
        img.setAttribute("alt", "")
    }
    // Run loop until no switching is needed
    while (switching) {
        switching = false;
        let rows = tableBody.getElementsByTagName(recordRowType);
        let sortLogicAscending
        let sortLogicDescending
        //Loop to go through all rows
        for (i = 0; i < (rows.length - 1); i++) {
            var Switch = false;
            // Fetch 2 elements that need to be compared
            if(recordRowType == "tr"){
                x = rows[i].children[n];
                y = rows[i + 1].children[n];
            }
            //Target the tbody's first row and get the column
            else{
                x = rows[i].firstElementChild.children[n]
                y = rows[i + 1].firstElementChild.children[n]
            }
            switch(typeOfSort){                
                case "text":
                    sortLogicAscending  = x.textContent.toLowerCase() > y.textContent.toLowerCase()
                    sortLogicDescending = x.textContent.toLowerCase() < y.textContent.toLowerCase()
                    break
                case "date":
                    sortLogicAscending = sortDateLogic(x.innerHTML, y.innerHTML, true)
                    sortLogicDescending = sortDateLogic(x.innerHTML, y.innerHTML, false)
                    break
                case "fileSize":
                    sortLogicAscending = parseInt(x.innerHTML.split(" ")[0]) > parseInt(y.innerHTML.split(" ")[0])
                    sortLogicDescending = parseInt(x.innerHTML.split(" ")[0]) < parseInt(y.innerHTML.split(" ")[0])
                    break
                case "tabularOnly":
                    sortLogicAscending = x.getAttribute('value') == 'false' && y.getAttribute('value') == 'true'
                    sortLogicDescending = x.getAttribute('value') == 'true' && y.getAttribute('value') == 'false'
                case "versionCheck":
                    sortLogicAscending = x.getAttribute('value') > y.getAttribute('value')
                    sortLogicDescending = x.getAttribute('value') < y.getAttribute('value')
            }
            // Check the direction of order
            if (direction == "ascending") {
                if(sortLogicAscending)
                // Check if 2 rows need to be switched              
                {
                    // If yes, mark Switch as needed and break loop
                    Switch = true;
                    break;
                }
            } else if (direction == "descending") {
                // Check direction
                if(sortLogicDescending)
                    {
                    // If yes, mark Switch as needed and break loop
                    Switch = true;
                    break;
                }
            }
        }
        if (Switch) {
            // Function to switch rows and mark switch as completed
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;

            // Increase count for each switch
            count++;
        } else {
            // Run while loop again for descending order
            if (count == 0 && direction == "ascending") {
                direction = "descending";
                switching = true;
            }
        }
    }
    //Change Icon here
    if(direction == "ascending"){        
        selectedSortImages.setAttribute("src", "static/images/caret-down-fill.svg")
        selectedSortImages.setAttribute("alt", "")
    }
    else if(direction == "descending"){
        selectedSortImages.setAttribute("src", "static/images/caret-up-fill.svg")
        selectedSortImages.setAttribute("alt", "")
    }
}

/***************End Sort logic***********************/

/***************End Table Functions*********************/

// This class contains all the necessary pieces to create a progress screen for either the import or delete actions
class ProgressDisplay {
    constructor() {
        this.progressBarSuccess = document.getElementById('progressBarSuccess')
        this.progressBarFail = document.getElementById('progressBarFail')
        this.progressTitle = document.getElementById('progressTitle')
        this.progressCounterMessage = document.getElementById('progressCounterMessage')
        this.progressListButtonText = document.getElementById('progressListButtonText')
        this.progressText = document.getElementById("progressText")
        this.progressContainer = document.getElementById("progressScreenContainer")
        this.progressList = document.getElementById("progressList")
        this.closeProgressModal = document.getElementById("closeProgressModal")
        this.progressListButton = document.getElementById("progressListButton")
        this.stopProgressButton = document.getElementById("stopProgress")
        this.errorDiv = document.getElementById("progressErrorDiv")
        this.toggleErrovDiv = document.getElementById("toggleProgressErrorDiv")
        this.timerDisplay = document.getElementById("timerCount")
    }

    progressScreenSetup(subfolders, action) {
        //Reset the display for loaded message and loading screen
        this.progressContainer.removeAttribute("style")
        this.stopProgressButton.removeAttribute("style")
        this.closeProgressModal.setAttribute("style", "display:none;")
        this.progressListButton.setAttribute("style", "display:none;")
        this.progressList.classList.remove("show")
        this.progressList.innerHTML = ""
        //Reset loading bar
        this.progressBarSuccess.classList.remove('bg-info')
        this.progressBarSuccess.setAttribute('style', 'width:2%')
        this.progressBarSuccess.setAttribute('aria-valuenow', '0')
        this.progressBarSuccess.setAttribute('aria-valuemax', `${subfolders.length}`)
        this.progressBarSuccess.classList.add("progress-bar-animated")
        //Reset failed loading bar
        this.progressBarFail.setAttribute('style', 'width:0%')
        this.progressBarFail.setAttribute('aria-valuenow', '0')
        this.progressBarFail.setAttribute('aria-valuemax', `${subfolders.length}`)
        this.progressBarFail.classList.add("progress-bar-animated")
        //Reset Error messages
        this.errorDiv.innerHTML = ""
        this.toggleErrovDiv.setAttribute("style", "display:none;")
        this.errorDiv.classList.remove("show")
        //Set the StopProgress buttons onClick function to include the action (either 'import' or 'delete')
        this.stopProgressButton.setAttribute("onClick", `stoppingProgress('${action}')`)
        //Set Progress Screen Image
        if (action == 'import') {
            document.getElementById('progressImgImport').removeAttribute('hidden')
            document.getElementById('progressImgDelete').setAttribute('hidden', '')
        } else {
            document.getElementById('progressImgDelete').removeAttribute('hidden')
            document.getElementById('progressImgImport').setAttribute('hidden', '')
        }
    }

    startTimer(){
        let elapsedTime
        this.timerDisplay.innerHTML = "00:00:00"
        var startTime = Date.now()
        this.timerDisplay = setInterval(function(){
            elapsedTime = Date.now() - startTime
            document.getElementById("timerCount").innerHTML = formatTime(elapsedTime)
        },
        1000)
    }

    stopTimer() {
        clearInterval(this.timerDisplay)
    }

}

/**Populates the text in the toggleProgressErrorDiv*/
function populateFailedProgressMessage(failedAreas, action){
    // call progressDisplay class constructor to define elements
    let progressDisplay = new ProgressDisplay()
    let p = document.createElement("p")
    if (progressDisplay.toggleErrovDiv.lastChild.tagName == "P"){
        progressDisplay.toggleErrovDiv.lastElementChild.remove()
    }
    let actionValue = action == 'import' ? "import" : "delete" // using a ternary operator
    p.innerHTML = `${Object.keys(failedAreas).length} areas have failed ${actionValue}.` // need to swap between import/delete wording
    progressDisplay.toggleErrovDiv.appendChild(p)
}

/**Populates a list of successfully imported/deleted areas on the progress screen*/
function populateSuccessfulProgressMessage(loadedAreas, action){
    // call progressDisplay class constructor to define elements
    let progressDisplay = new ProgressDisplay()
    //set attributes
    progressDisplay.closeProgressModal.removeAttribute("style")
    if(loadedAreas.length > 0){
        progressDisplay.progressListButton.removeAttribute("style")
    }
    progressDisplay.stopProgressButton.setAttribute("style", "display:none;")
    progressDisplay.progressList.innerHTML = ""
    for(folder in loadedAreas){
        //define elements
        let div = document.createElement("div")
        let img = document.createElement("img")
        let p = document.createElement("p")
        //set values
        let actionValue = action == 'import' ? "imported" : "deleted" // using a ternary operator
        p.innerHTML = `${loadedAreas[folder]} successfully ${actionValue}.` // need to swap between import/delete wording
        img.setAttribute("src", "static/images/checkmarkFillGreen.svg")
        div.append(img)
        div.appendChild(p)
        progressDisplay.progressList.appendChild(div)
    }
}

function stoppingProgress(action){
    // call progressDisplay class constructor to define elements
    let progressDisplay = new ProgressDisplay()
    progressDisplay.progressBarSuccess.setAttribute('style', 'width:100%;')
    progressDisplay.progressBarSuccess.classList.add("bg-info")
    progressDisplay.progressTitle.innerHTML = `Stopping ${action}...`
    stopProgress = true
}

async function importCandidates(skipPretest = true,  loadInSpatialOrder = false, loadspatialdatawithinsubprocess = false, isDissolve = true, includeSubRules = false){
    //set values
    stopProgress = false
    subfolders = importTable.selectedCheckboxes
    let containsDuplicateSSA = checkForDuplicateSSA(subfolders) //A check to see if the user is trying to import duplicate AOIs within an import action
    if(containsDuplicateSSA){
        return
    }
    let overrideExistingSSA = await checkForExistingSSA()
    action = "import"
    //If no duplicates are found:
    let progressDisplay = new ProgressDisplay()
    if(overrideExistingSSA){
        // call progressDisplay class constructor to define elements
        // resets the initial values for the Progress Screen display variables
        $("#progressScreen").modal("toggle")
        progressDisplay.progressScreenSetup(subfolders, action);
        // set values for function-specific text & messages
        progressDisplay.progressTitle.innerHTML = "Importing data..."
        progressDisplay.progressCounterMessage.innerHTML = `0 out of ${subfolders.length} imports loaded`
        progressDisplay.progressListButtonText.innerHTML = "Click to see list of imported areas"
        //Define scope variables
        let successfulFolders = []
        let failedFolders = []
        let successCounter = 0
        let failedCounter = 0
        //Determine tabular only
        isTabularOnly = document.getElementById('loadTabularData').checked
        /*
        //This functionality will be implemented Post Prototype.
        TODO: Enable spatial sort in SSURGO Portal UI
        //Determine spatial sorting
        loadInSpatialOrder = document.getElementById('spatialSort').checked*/
        //Determine if the user is not dissolving
        isDissolve = !document.getElementById('dissolve').checked
        includeSubRules = document.getElementById('includeInterpretationSubRules').checked
        progressDisplay.startTimer()
        for(folder in subfolders){
            /*Stop button has a function. This function sets a global variable that will need to be reset at the end of the cancelation*/
            if(stopProgress != true){
                progressDisplay.progressText.innerHTML = `Importing ${subfolders[folder]} into your database...`
                request = {
                    'request': importCandidatesRequest, 'database': databasePath, 'root' : folderPath, 'skippretest': skipPretest, 'istabularonly': isTabularOnly, 'loadinspatialorder' : loadInSpatialOrder,
                    'loadspatialdatawithinsubprocess' : loadspatialdatawithinsubprocess, 'dissolvemupolygon' : isDissolve, 'subfolders' : [subfolders[folder]], 'includeinterpretationsubrules' : includeSubRules
                }
                let response = await sendData(request)
                //Response is good
                if (response.status){
                    successfulFolders.push(subfolders[folder])
                    successCounter += 1
                    progressDisplay.progressCounterMessage.innerHTML = `${successCounter} out of ${subfolders.length} imports loaded. ${failedCounter} imports failed.`
                    progressDisplay.progressBarSuccess.setAttribute('aria-valuenow', `${successCounter}`)
                    let width = (successCounter * 100) / subfolders.length
                    progressDisplay.progressBarSuccess.setAttribute('style', `width:${width}%`)
                }
                //If the import response has a status of false
                else{
                    let errorData = {"areaname": subfolders[folder], "errormessage": response.errormessage}
                    failedFolders.push(errorData)
                    failedCounter += 1
                    progressDisplay.progressCounterMessage.innerHTML = `${successCounter} out of ${subfolders.length} imports loaded. ${failedCounter} imports failed.`
                    progressDisplay.progressBarFail.setAttribute('aria-valuenow', `${failedCounter}`)
                    let width = (failedCounter * 100) / subfolders.length
                    progressDisplay.progressBarFail.setAttribute('style', `width:${width}%`)
                    populateErrorMessage(errorData, false)
                }
            }
            //Import process stopped
            else{
                echo('Stopped import')
                break
            }
        }
        progressDisplay.stopTimer()
        if(Object.keys(failedFolders).length > 0){
            progressDisplay.toggleErrovDiv.removeAttribute("style")
            progressDisplay.progressBarFail.classList.remove("progress-bar-animated")
            populateFailedProgressMessage(failedFolders, action)
        }
        progressDisplay.progressBarSuccess.classList.remove("progress-bar-animated")
        populateSuccessfulProgressMessage(successfulFolders, action)
        await selectDatabase(databasePath.slice(0, (-databaseName.length - 1)), databasePath)
        //Navigate the table view to default to the database table
        document.getElementById("databaseNavLink").click()
    }
}

/**A method that checks if the user is trying to import duplicate areasymbols. It takes a list of import candidates and checks it against duplicateSSAs */
function checkForDuplicateSSA(importCandidates){
    let modalBody = document.getElementById("duplicateSSAModalMessage")
    modalBody.innerText = ""
    for(i in Object.keys(duplicateSSAs)){
        let areaSymbol = Object.keys(duplicateSSAs)[i]
        let duplicateSSAFolder = Object.values(duplicateSSAs)[i]
        let duplicateList = importCandidates.filter(function(e) {
            return duplicateSSAFolder.includes(e)        
        })
        if(duplicateList.length > 1){
            let p = document.createElement("p")
            p.innerHTML = `The areasymbol <b>${areaSymbol}</b> is found in the following selected folders: <b>${duplicateList.join(", ")}</b>.`
            modalBody.append(p)
        }
    }
    if(modalBody.innerText != ""){
        $("#duplicateSSAModal").modal("toggle")
        return true
    }
    else{
        return false
    }
}

/**Create a promise that listens for a button click on two buttons */
async function awaitUserInput(cancelButtonId, continueButtonId){
    let cancelButton = document.getElementById(cancelButtonId)
    let continueButton = document.getElementById(continueButtonId)
    function buildPromise(){
        let decisionMade = new Promise((resolve) => {
            continueButton.addEventListener("click", function(){
                resolve(true)
            })
            cancelButton.addEventListener("click", function(){
                resolve(false)
            })
        })
        return decisionMade
    }
    let promise = buildPromise()
    let promiseResult = await promise
    return promiseResult
}

async function checkForExistingSSA(){
    let existingCheckboxItems = []
    let continueImport
    for(checkbox in importTable.selectedCheckboxes){
        if(document.getElementById(`importCheckbox${importTable.selectedCheckboxes[checkbox]}`).parentNode.parentNode.children.item(6).innerText != ""){
            existingCheckboxItems.push(importTable.selectedCheckboxes[checkbox])
        }
        
    }
    if(existingCheckboxItems.length > 0){        
        $("#existingSSAModal").modal("toggle")
        let modalBody = document.getElementById("existingSSAModalMessage")
        if(existingCheckboxItems.length > 1){
            modalBody.innerHTML = `These folders contain areasymbol(s) that are already in the database: ${existingCheckboxItems.join(", ")}.`
        }
        else{
            modalBody.innerHTML = `This folder contains areasymbol(s) that are already in the database: ${existingCheckboxItems}.`
        }
        continueImport = await awaitUserInput("cancelExistingImport", "continueExistingImport")
        return continueImport  
    }
    return true
}

async function deleteDatabaseWarning(){
    let continueImport
    if(databaseTable.selectedCheckboxes.length == databaseTable.totalRows){
        $("#deleteWarningModal").modal("toggle")
        let modalBody = document.getElementById("deleteDatabaseMessage")
        modalBody.innerHTML = "You are getting ready to delete all of the Area Symbols in your database: " + databaseName
        continueImport = await awaitUserInput("cancelDelete", "continueDelete")
        return continueImport   
    }    
    return true
}

async function deleteCandidates(){
    //set values
    stopProgress = false
    subfolders = databaseTable.selectedCheckboxes
    action = "delete"
    let continueDelete = await deleteDatabaseWarning()
    if(!continueDelete){
        return
    }
    // call progressDisplay class constructor to define elements
    let progressDisplay = new ProgressDisplay()
    $("#progressScreen").modal("toggle")
    // resets the initial values for the Progress Screen display variables
    progressDisplay.progressScreenSetup(subfolders, action);
    // set values for function-specific text & messages
    progressDisplay.progressTitle.innerHTML = "Deleting data..."
    progressDisplay.progressCounterMessage.innerHTML = `0 out of ${subfolders.length} records deleted`
    progressDisplay.progressListButtonText.innerHTML = "Click to see list of deleted areas"
    //Define scope variables
    let successfulFolders = []
    let failedFolders = []
    let successCounter = 0
    let failedCounter = 0
    //Determine tabular only
    isTabularOnly = document.getElementById('loadTabularData').checked
    progressDisplay.startTimer()
    for(folder in subfolders){
        /*Stop button has a function. This function sets a global variable that will need to be reset at the end of the cancelation*/
        if(stopProgress != true){
            progressDisplay.progressText.innerHTML = `Deleting ${subfolders[folder]} from your database...`
            deleteRequest = {
                'request': deleteAreaSymbolRequest, 'database': databasePath, 'areasymbols' : [subfolders[folder]]
            }
            let response = await sendData(deleteRequest)
            //Response is good
            if (response.status){
                successfulFolders.push(subfolders[folder])
                successCounter += 1
                progressDisplay.progressCounterMessage.innerHTML = `${successCounter} out of ${subfolders.length} records deleted. ${failedCounter} deletes failed.`
                progressDisplay.progressBarSuccess.setAttribute('aria-valuenow', `${successCounter}`)
                let width = (successCounter * 100) / subfolders.length
                progressDisplay.progressBarSuccess.setAttribute('style', `width:${width}%`)
            }
            //If the import response has a status of false
            else{
                let errorData = {"areaname": subfolders[folder], "errormessage": response.errormessage}
                failedFolders.push(errorData)
                failedCounter += 1
                progressDisplay.progressCounterMessage.innerHTML = `${successCounter} out of ${subfolders.length} records deleted. ${failedCounter} deletes failed.`
                progressDisplay.progressBarFail.setAttribute('aria-valuenow', `${failedCounter}`)
                let width = (failedCounter * 100) / subfolders.length
                progressDisplay.progressBarFail.setAttribute('style', `width:${width}%`)
                populateErrorMessage(errorData, false)
            }
        }
        else { //Import process stopped
            echo('Stopped import')
            break
        }
    }
    progressDisplay.stopTimer()
    if(Object.keys(failedFolders).length > 0){
        progressDisplay.toggleErrovDiv.removeAttribute("style")
        progressDisplay.progressBarFail.classList.remove("progress-bar-animated")
        populateFailedProgressMessage(failedFolders, action)
    }
    progressDisplay.progressBarSuccess.classList.remove("progress-bar-animated")
    populateSuccessfulProgressMessage(successfulFolders, action)
    databaseTable.selectedCheckboxes = []
    await selectDatabase(databasePath.slice(0, (-databaseName.length - 1)), databasePath)
}

function setDatabaseName(path){
    databaseName = path.split('/')
    databaseName = databaseName[databaseName.length-1]
    document.getElementById('selectedDatabaseNameTopHeader').innerHTML = databaseName
    document.getElementById('selectedDatabaseNameTopHeader').setAttribute('title', databasePath.replaceAll("/", "\\"))
    document.getElementById('selectedDatabaseNameLeftPaneTitle').innerHTML = "Change or Create a Database"
    document.getElementById('selectedDatabaseNameLeftPane').setAttribute('placeholder', databaseName)
    $('#selectDatabasePage').toggle(); //toggle display off
    $('#homePageContainer').toggle(); //toggle display on
    document.getElementById('selectedFolderNameBrowseBtn').disabled = false
}

function setFolderName(path){
    folderName = path.split('/')
    if(folderName[folderName.length -1] == ""){
        folderName.pop()
    }
    folderName = folderName[folderName.length-1]
    document.getElementById('selectedFolderNameTitle').innerHTML = "Change Location of SSURGO Data"
    document.getElementById('selectedFolderName').setAttribute('placeholder', folderName)
}

// Gets the Database Template Catalog from the config file by executing the 'getTemplateCatalog' request
async function getDatabaseTemplateCatalog() {
    var templateCatalogRequest = {'request' : getTemplateCatalogRequest}
    sendData(templateCatalogRequest)
}

/**Iterate through the template config options stored in 'emptyTemplates' & populate Database Type Dropdown menu*/
function populateDatabaseTypeDropdown(){
    var showTextTemplates = document.getElementById('textTemplatesCheckbox').checked
    var templateOptions = document.getElementById('templateTypeDropdown')
    templateOptions.innerHTML = ""
    for (template in emptyTemplates)
    {
        if (showTextTemplates) {
            if (emptyTemplates[template].textTemplate == true) {
                let option = document.createElement('option')
                option.value = emptyTemplates[template].path
                option.ariaLabel = template
                option.innerHTML = template
                templateOptions.appendChild(option)
            }
        } else {
            if (emptyTemplates[template].textTemplate == false) {
                let option = document.createElement('option')
                option.value = emptyTemplates[template].path
                option.ariaLabel = template
                option.innerHTML = template
                templateOptions.appendChild(option)
            }
        }
    }
    // Calls displayNewDatabasePath() everytime the "Create New Database" button is clicked
    displayNewDatabasePath();
}

/**Concatenates the user's directory, database name & extension and then displays it to the user when creating a new DB*/
async function displayNewDatabasePath() {
    // Directory where database will be created
    let userDirectory = updatedValue('databaseTextBox');

    // DB Name
    let createNewDatabaseName = updatedValue('createNewDatabaseName');

    // DB Extension
    let templateValue = document.getElementById('templateTypeDropdown');
    let extension = "";

    //DB Error Message
    let errorMessageElement = document.getElementById("createNewDatabaseErrorMessage")
    errorMessageElement.innerHTML = ""

    if (templateValue != null)
    {
        if (templateValue.options[templateValue.selectedIndex] != undefined)
        {
            let selectedTemplate = templateValue.options[templateValue.selectedIndex].text;
            extension = emptyTemplates[selectedTemplate].suffix;
        }
    }
    //Standardize the file path presented
    userDirectory = userDirectory.split("/")
    userDirectory = userDirectory.join("\\")
    // Build out full path & display it to the user. Also sets the databasePath global Variable
    if(userDirectory.endsWith("\\")){
        var newDatabaseCreationDisplay = userDirectory + createNewDatabaseName + extension;
    }
    else{
        var newDatabaseCreationDisplay = userDirectory + "\\" + createNewDatabaseName + extension;
    }

    // Define elements
    let createNewDatabaseLocation = document.getElementById('createNewDatabaseLocation');
    let overwriteWarningContainer = document.getElementById('overwriteWarningContainer');
    let overwriteCheckbox = document.getElementById('overwriteCheckbox');
    let createNewDbBtn = document.getElementById("createNewDbBtn");

    //Disable "Save Button" if database name is blank
    if(createNewDatabaseName == ""){
        createNewDbBtn.disabled = true
    }
    else{
        createNewDbBtn.disabled = false
    }

    //execute request to check if it database already exists
    await fetch(fileCheckUrl, {
        method : 'POST',
        headers: {'Content-Type' : 'application/json'},
        body: JSON.stringify(newDatabaseCreationDisplay)},
        //then we make sure the response is in JSON and make a JSON object
    ).then(response =>response.json())
    .then(function(response){
        if(response) { //Database already exists
            createNewDbBtn.disabled = true // Disable "Save Database" button
            createNewDatabaseLocation.innerHTML = newDatabaseCreationDisplay;
            createNewDatabaseLocation.setAttribute('style', 'color: #FF0000') //Change text to red
            overwriteWarningContainer.setAttribute('style', 'display: block') //Display overwriteWarningContainer
            databasePath = newDatabaseCreationDisplay.replaceAll('\\', '/');
            if (overwriteCheckbox.checked)
            {
                overwriteChecked = true
                if(createNewDatabaseName != ""){
                    createNewDbBtn.disabled = false //Re-enable "Save Database" button when "overwrite database" checkbox is checked
                }
            }
        }
        else { //Database doesn't already exist
            if(createNewDatabaseName == ""){
                createNewDbBtn.disabled = true //Enable "Save Database" button
            }
            createNewDatabaseLocation.innerHTML = newDatabaseCreationDisplay;
            createNewDatabaseLocation.setAttribute('style', 'color: #000000') //Change text to black
            overwriteWarningContainer.setAttribute('style', 'display: none') //Don't display overwriteWarningContainer
            overwriteChecked = false
            databasePath = newDatabaseCreationDisplay.replaceAll('\\', '/');
        }
    })
}

/**Creates a new template database at the location the user picks*/
async function createNewTemplateDatabase(template, destinationFolder, dbName, overwrite = overwriteChecked) {
    let templateValue = document.getElementById(template);
    let selectedTemplate = templateValue.options[templateValue.selectedIndex].text;
    let destinationFolderValue = document.getElementById(destinationFolder).value;
    //Send folder path using / to prevent errors on the python side.
    destinationFolderValue = destinationFolderValue.replaceAll("\\", "/")
    let dbNameValue = document.getElementById(dbName).value;
    let errorMessageElement = document.getElementById("createNewDatabaseErrorMessage")
    document.getElementById('overwriteCheckbox').checked = false // Always uncheck "overwrite checkbox" after creating new database
    setCookie(databaseTableRequest, destinationFolderValue, 365)

    var createNewDatabase = {'request' : copyTemplateFileRequest, 'templatename' : selectedTemplate, 'folder' : destinationFolderValue,
        'filename' : dbNameValue, 'overwrite' : overwrite}
    let response = await sendData(createNewDatabase) // Creates new Database
    //Check status of response.
    if (response.status == true) {
        selectDatabase(destinationFolderValue, databasePath) // Sets newly created database as the Selected Database
        $("#createNewDatabaseModal").modal("hide") //Only if successful, dismiss the page
        document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //close the help menu if it was open before navigating away
    }
    //Populate error message on createNewDatabaseModal
    else{
        errorMessageElement.innerHTML = ""
        let i = document.createElement("i")
        i.innerText = response.errormessage.replaceAll("/", "\\")
        errorMessageElement.appendChild(i)
    }
}

//Documentation at Mozilla states that the unload event suite should not be used and is not reliably executed.
        // The pagehide has not been thoroughly tested on my end however
        //The sendBeacon seems to work even after being idle for extended periods of time.
window.addEventListener('pagehide', function(){
    navigator.sendBeacon('http://localhost:8083/close', killServer())
})

//Send any unhandled errors to the log file. NOTE: STACK IS NONSTANDARD and should only be used as a last resort.
//Potential errors should be placed inside of a try/catch block in order to avoid this catch all.
window.addEventListener('error', e => {
        logJavaScriptError(e.error.stack)
})

//Log errors that occured in a promise statement
window.addEventListener('unhandledrejection', e =>{
    logJavaScriptError(e.reason.stack)
})

//Present a warning to users when trying to navigate away.
window.onbeforeunload = function(){
    return "Are you sure you want to leave this page?"
}

//When the webpage first loads, check to see if the server is running. Then issue a request to populate the tree view under the create database tab
window.onload = async function(){    
    await fetch(
        "http://localhost:8083/serverStatus",
        {
            method : 'POST', 
            headers: {'Content-Type' : 'application/json'}, 
            body: JSON.stringify(data),
        }
    ).catch(function(){
        $('#serverClosedModal').modal("show")
    })  
    await getDatabaseTemplateCatalog() 
    document.getElementById("pageTitle").innerHTML = "SSURGO Portal - v" + getCookie("ApplicationVersion") 
}

//Send data to server to self terminate {Not sure if data actually needs to be sent to server. Hitting the route seems to be sufficient}
function killServer(){
    data = {'action' : 'killServer'}
    JSON.stringify(data)
    console.log('Kill server')
}

/**Used to select all checkboxes.*/
function selectDeselectAll(elementClass, masterCheckbox){
    let master = document.getElementById(masterCheckbox)
    var checkboxes = document.getElementsByClassName(elementClass);
    if(master.checked){
        for(var i=0; i<checkboxes.length; i++){
            if(checkboxes[i].type=='checkbox'){
                checkboxes[i].checked=true;
            }
        }
    }
    else{
        for(var i=0; i<checkboxes.length; i++){
            if(checkboxes[i].type=='checkbox')
                checkboxes[i].checked=false;
        }
    }
    if(elementClass == 'dataCheckbox'){
        getSelectedCheckboxes(dbTableId)
    }
    else{
        getSelectedCheckboxes(importTableId)
    }
}

/*************************************************************Cookie Functions*********************************** */
/**Checks to see if cookie exists */
function cookieExists(cookieName){
    let cookieSet = getCookie(cookieName)
    if(cookieSet != undefined){
        return true
    }
    else{
        return false
    }
}
/**Set cookie*/
function setCookie(cname, cvalue, exdays){
    if (cvalue == undefined)
    {
        cvalue = "C:/"
    }
    const d = new Date()
    d.setTime(d.getTime() + (exdays*24*60*60*1000))
    let expires = "expires=" + d.toUTCString()
    document.cookie = `${cname} = ${cvalue}; ${expires}`
}
/**Return cookie */
function getCookie(cname){
    let cookie = {}
    document.cookie.split(';').forEach(function(el){
        let [key,value] = el.split('=')
        cookie[key.trim()] = value
    })
    return cookie[cname];
}
/************End cookie functions******************/

/**Used to return the current time Format is hh:mm:ss.ms*/
function currentTime(){
    var time = new Date()
    var displayTime = time.getHours() + ":" + time.getMinutes() + ":" + time.getSeconds() + "." + time.getMilliseconds()
    return displayTime
}

//---------------------Help Pane toggles-------------------------
async function toggleContactUs() {
    //contactUsHelpPaneContent is the id for the ContactUs content found in the HTML file
    toggleHelpPaneContent('contactUsHelpPaneContent')

    // send request out to get the log file
    await fetch("http://localhost:8083/logFile", {
        method : 'GET'
    }).then((response) => response.text())
    .then(function(text){
        document.getElementById('logFileLocation').innerHTML = text.toString()
    })
}

function toggleHelpPaneContent(elementId) {
    let helpPaneContainerParent = document.getElementById('helpPaneContainer')
    let helpPageContainers = helpPaneContainerParent.querySelectorAll('.helpPageContainer');
    helpPageContainers.forEach(function(node) {
        node.setAttribute('style', 'display: none')
    })

    let toggledContent = document.getElementById(elementId)
    toggledContent.setAttribute('style', 'display: block')

    document.getElementById("applicationVersion").innerHTML = getCookie("ApplicationVersion") 
    document.getElementById("sqliteSSURGOTemplateVersion").innerHTML = getCookie("SQLiteSSURGOTemplateVersion") 
    document.getElementById("ssurgoVersion").innerHTML = getCookie("SSURGOVersion")
}

$(".helpPaneBtn").click(function(){
    let clickedButton = this.id
    $(".helpPaneContainer").toggle();
    $("#closeHelpMenu").focus()
    //Set a value to refocus the previous element after closing the element.
    $("#closeHelpMenu").attr("previousFocus", clickedButton)    
})

$("#closeHelpMenu").click(function(){
    $(".helpPaneContainer").toggle();
    let previousFocus = $("#closeHelpMenu").attr("previousFocus")
    $(`#${previousFocus}`).focus()
})

/*Rotates image when sub header section is expanded */
$(".containsSubHeaders").click(function(){
    if($(this).find("> button").attr("aria-expanded") == 'true'){
        //Targetting the direct child button's direct child image
        $(this).find('> button').find('> img').css("transform", "rotate(180deg)")
    }
    else{
        $(this).find('> button').find('> img').css("transform", "rotate(90deg)")
    }
})

/*Rotates the Expand the help menu image */
$("#expandHelpMenu").click(function(){
    if($(this).attr('status') == 'colapsed'){
        $(this).attr('status', 'expanded')
        $(this).find('img').css('transform', 'rotate(90deg)')
        $(this).find('img').attr('alt', 'Colapse Help Menu Icon')
        $(".helpPaneContainer").width("100%")
    }
    else{
        $(this).attr('status', 'colapsed')
        $(this).find('img').css('transform', 'rotate(-90deg)')        
        $(this).find('img').attr('alt', 'Expand Help Menu Icon')
        $(".helpPaneContainer").width("350px")
    }
})
//-------------------------Switch input toggles----------------------
function togglePath(clickableContainer, editableContainer){
    $(`#${clickableContainer}`).toggle()
    $(`#${editableContainer}`).toggle()
}

$("#newDisplayTreePath").click(function(){
    togglePath("newClickablePathContainer", "newDatabaseTextBox")
    if($(this).find('img').attr('src') == '/static/images/changePathToEdit.svg'){
        $(this).find('img').attr('src', '/static/images/closeIcon.svg')
        $(this).attr("style", "top:2px;")
    }
    else{
        $(this).find('img').attr('src', '/static/images/changePathToEdit.svg')
        $(this).attr("style", "top:-5px;")
    }
})

$("#displayTreePath").click(function(){
    togglePath("clickablePathContainer", "databaseTextBox")
    if($(this).find('img').attr('src') == '/static/images/changePathToEdit.svg'){
        $(this).find('img').attr('src', '/static/images/closeIcon.svg')
        $(this).attr("style", "top:2px;")
    }
    else{
        $(this).find('img').attr('src', '/static/images/changePathToEdit.svg')
        $(this).attr("style", "top:-5px;")
    }
})

$("#displayTreePathModal").click(function(){
    togglePath("clickablePathContainerModal", "databaseTextBoxModal")
    if($(this).find('img').attr('src') == '/static/images/changePathToEdit.svg'){
        $(this).find('img').attr('src', '/static/images/closeIcon.svg')
        $(this).attr("style", "top:2px;")
    }
    else{
        $(this).find('img').attr('src', '/static/images/changePathToEdit.svg')
        $(this).attr("style", "top:-5px;")
    }
})

$("#ssaDisplayTreePath").click(function(){
    togglePath("ssaClickablePathContainer", "ssaTextBox")
    if($(this).find('img').attr('src') == '/static/images/changePathToEdit.svg'){
        $(this).find('img').attr('src', '/static/images/closeIcon.svg')
        $(this).attr("style", "top:2px;")
    }
    else{
        $(this).find('img').attr('src', '/static/images/changePathToEdit.svg')
        $(this).attr("style", "top:-5px;")
    }
})

//---------------------Select Database & Select Parent SSA Folder Page Toggles---------------------
//Toggle to display the Select Database Page
$("#selectDatabaseBrowseBtn").click(function(){
    $("#selectDatabasePage").toggle() //toggle display on
    $("#homePageContainer").toggle() //toggle display off
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //don't display help menu if it was previously open
})

//Toggle to close the Select Database Page
$("#selectDatabasePageBackBtn").click(function(){
    $("#selectDatabasePage").toggle() //toggle display off
    $("#homePageContainer").toggle() //toggle display on
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //don't display help menu if it was previously open
})

//Toggle to display the Select SSA Parent Folder Page
$("#selectedFolderNameBrowseBtn").click(function(){
    $("#selectSSAPage").toggle() //toggle display on
    $("#homePageContainer").toggle() //toggle display off
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //don't display help menu if it was previously open
})

//Toggle to close the Select SSA Parent Folder Page when the Finalize button is clicked
$("#selectSsurgoFolderFinalizeBtn").click(function(){
    $("#selectSSAPage").toggle() //toggle display off
    $("#homePageContainer").toggle() //toggle display on
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //don't display help menu if it was previously open
})

//Toggle to close the Select SSA Parent Folder Page
$("#selectSSAPageBackBtn").click(function(){
    $("#selectSSAPage").toggle() //toggle display off
    $("#homePageContainer").toggle() //toggle display on
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //don't display help menu if it was previously open
})

//Toggle to close the Progress Modal by clicking the 'Next' Button
$("#closeProgressModal").click(function(){
    $("#homePageContainer").toggle() //toggle display on
    $("#selectDatabasePage").toggle() //toggle display off
    document.getElementById('helpPaneContainer').setAttribute("style", "display: none") //don't display help menu if it was previously open
})

//---------------------Tree View Search bar toggles-------------------------
//Toggle search field for Create New Database
$("#newDatabaseSearchBtn").click(function(){
    $("#newDatabaseSearchBtn").toggle()
    $("#newDatabaseSearch").toggle()
})
$("#newDatabaseSearchTextBtn").click(function(){
    $("#newDatabaseSearch").toggle()
    $("#newDatabaseSearchBtn").toggle()
})

//Toggle search field for Existing Database
$("#databaseSearchBtn").click(function(){
    $("#databaseSearchBtn").toggle()
    $("#databaseSearch").toggle()
})

$("#databaseSearchTextBtn").click(function(){
    $("#databaseSearch").toggle()
    $("#databaseSearchBtn").toggle()
})

//Toggle search field for Existing Database Modal
$("#databaseSearchBtnModal").click(function(){
    $("#databaseSearchBtnModal").toggle()
    $("#databaseSearchModal").toggle()
})
$("#databaseSearchTextBtnModal").click(function(){
    $("#databaseSearchModal").toggle()
    $("#databaseSearchBtnModal").toggle()
})
//Toggle search field for SSA Modal
$("#ssaSearchBtn").click(function(){
    $("#ssaSearchBtn").toggle()
    $("#ssaSearchContainer").toggle()
})
$("#ssaSearchTextBtn").click(function(){
    $("#ssaSearchContainer").toggle()
    $("#ssaSearchBtn").toggle()
})

//--------------Toggles for Advanced Options--------------
$("#importNavLink").click(function(){
    $("#importOptionsContainer").show()
    $("#databaseOptionsContainer").hide()
})

$("#databaseNavLink").click(function(){
    $("#importOptionsContainer").hide()
    $("#databaseOptionsContainer").show()
})

//--------------Toggle for Text Templates Warning Message------------
$("#textTemplatesCheckbox").click(function(){
    $("#textTemplatesWarningContainer").toggle()
})

// Initialize all instances of Popover
var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl)
})

//--------------------General Functions----------------------

/**Convert date object, returned by the Data Loader, into a MM/DD/YYYY format.*/
function formatDate(date){
    let unformattedDate = new Date(date)
    let month = unformattedDate.getMonth() + 1
    let day = unformattedDate.getDate()
    let year = unformattedDate.getFullYear()
    return (`${month}/${day}/${year}`)
}
/** Converts ms into a readable format (hh:mm:ss) */
function formatTime(time){
    let seconds = Math.round(time / 1000)
    let mins = Math.floor(seconds / 60)
    let hours = Math.floor(mins / 60)

    seconds = seconds % 60
    mins = mins % 60
    const readableTime = [
        hours.toString().padStart(2, "0"),
        mins.toString().padStart(2, "0"),
        seconds.toString().padStart(2, "0"),
    ].join(":")

    return readableTime
}

/**Adds a listener to the element that triggers the click function when the enter key is pressed*/
function addEnterEventListener(element){
    element.addEventListener("keypress", function(e){                    
        if(e.key == "Enter"){
            $(this).trigger("click")
        }               
    })
}

/**Adds button functionality to elements that normaly would not have this. I.E. a table row is now tabbable and an enter key will trigger the on click event*/
function addButtonFunctionality(element){
    element.setAttribute("tabindex", 0)
    element.setAttribute("role", "button")
    addEnterEventListener(element)
}

/**For debugging. Simple console.log() action.*/
function echo(message){
    console.log(message)
}