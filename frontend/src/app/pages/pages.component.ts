import {ChangeDetectorRef, Component, OnInit, SecurityContext} from "@angular/core";
import {FormControl, Validators} from "@angular/forms";
import {map, Observable, startWith} from "rxjs";
import {UserService} from "../@core/service/user.service";
import {MatDialog} from "@angular/material/dialog";
import {DialogSchemaComponent} from "./dialog/dialog-schema/dialog-schema.component";
import {CommonService} from "../@core/service/common.service";
import {SchemaService} from "../@core/service/schema.service";
import {Schema} from "../@core/model/user.model";
import {FileInfo, Level, SchemaStru} from "../@core/model/schema.model";
import {AttrLevel, FileInfoStru} from "../@core/model/files.model";
import {FilesService} from "../@core/service/files.service";
import {closest, distance} from "fastest-levenshtein";

@Component({
  selector: 'app-pages',
  templateUrl: './pages.component.html',
  styleUrls: ['./pages.component.scss'],
  providers: [UserService, SchemaService, CommonService, FilesService]
})
export class PagesComponent implements OnInit{
  constructor(private cd: ChangeDetectorRef,
              private userService:UserService,
              private schemaService: SchemaService,
              private commonService: CommonService,
              private filesService: FilesService,
              public dialog: MatDialog ) { }

  tabIdx: number = 0;
  userId: string = '';
  schemaId: string = '';
  schema = new FormControl<Schema>(null, [Validators.required]);
  files = new FormControl<string>('', [Validators.required]);
  schemaList: Schema[];
  methodList: string[] = ['FST', 'Langchain-OutputParsing'];
  fileTypeList: string[] = ['文本', '表單', '表格', '財務報表'];
  filteredSchemaList: Observable<Schema[]>;
  selectedSchema = null;
  selectedFiles: File[];
  uploadFiles: File[] = [];

  schemaOpenState = false;
  markedOpenState = false;

  min_support: number = 0.5;
  pattern_min: number = 2;
  pattern_max: number = 10;

  tokens = [
    {name: 'Basic symbol', checked: false},
    {name: 'Number', checked: false},
    {name: 'Duplicate characters', checked: false},
    {name: 'Limit pattern length', checked: false}
  ]
  removedList: string[] = [];
  patternList: string[] = [];
  selectedList: string[] = [];
  removedLen: number = 0;
  patternLen: number = 0;
  selectedLen: number = 0;
  selectRemoved: string[] = [];
  selectPatterns: string[] = [];
  selectSelected: string[] = [];

  selectOne = null;
  choosePatterns: string[] = [];
  selectedPattern: string[] = [];

  schemaStructure: object;

  attribute: string = '';
  selectAttr: string = '';
  attrList: string[] = [];

  dataTypeList: string[] = ['String', 'Array'];
  selectDataType = this.dataTypeList[0];

  levelList: Level[] = [
    {name: 'Level 1', value: '1'},
    {name: 'Level 2', value: '2'}
  ];
  selectLevel = this.levelList[0];
  selectPreAttr: string = '';

  selectSchemaForMarked = null;
  selectMethodForMarked = 'FST';
  selectFileTypeForMarked = null;
  selectFileForMarked: FileInfo = null;
  fileList: FileInfo[] = [];
  selectedFileTest: File;
  selectSchemaInfo: SchemaStru;
  selectFileInfo: FileInfoStru;

  selectAttrOfMain: AttrLevel = null;
  selectAttrOfSub: string = "";
  mainAttrList: AttrLevel[] = [];
  subAttrList: string[] = [];
  subAttrDisplay: boolean = true;
  pdfStructure: object;
  pdfPositionColor: object;
  selectedText: object = {text: "", start: -1, end: -1};
  pdfText: string = "";

  ngOnInit() {
    this.schemaOpenState = true;
    this.userService.getSchemaList(this.userId)
      .subscribe(data => {
        console.log(data);
        this.schemaList = data;
        this.filteredSchemaList = this.schema.valueChanges.pipe(
          startWith(''),
          map(value => {
            return this.schemaList.slice();
          }),
        );
      });
  }

  displayFn(schema: Schema) {
    return schema && schema.name ? schema.name : '';
  }

  displaySchema() {
    let schema_name = this.schemaList.find(e => e.id === this.selectedSchema).name
    this.schemaService.getDtd(this.selectedSchema)
      .subscribe( data => {
        let schemaStructure = "";
        if (data !== "")
          schemaStructure = JSON.parse(data);
        this.cd.detectChanges();
        const dialogRef = this.dialog.open(DialogSchemaComponent, {
          width: '800px',
          data: {title: schema_name, content: schemaStructure },
        });
        console.log(schemaStructure);
      });
  }

  onFileInput(event): void {
    this.selectedFiles = <File[]>event.target.files;
    let filesName = '';
    let cannotUpload = '';
    let fileIdx = 0;
    let haveWrongFile = false;
    for (let i = 0; i < this.selectedFiles.length; i++) {
      let fileName = this.selectedFiles[i].name;
      if (fileName.substring(fileName.lastIndexOf('.')) === '.pdf') {
        this.uploadFiles[fileIdx] = <File> this.selectedFiles[i];
        fileIdx = fileIdx + 1;

        if (i === 0) {
          filesName = event.target.files[i].name;
        } else if (i <= 2) {
          filesName = filesName + ',' + event.target.files[i].name;
        } else if (i === 2) {
          filesName = filesName + '...';
        }
      } else {
        cannotUpload = cannotUpload + ';' + fileName;
        haveWrongFile = true;
      }
    }
    if (haveWrongFile) {
      window.alert('Wrong file: ' + cannotUpload);
    }
    this.files.setValue(filesName);
  }

  selectAll() {
    this.tokens.forEach(t => t.checked = !t.checked);
    console.log(this.tokens);
  }

  updateToken(token_name:string) {
    this.tokens.find(e => e.name === token_name).checked = !this.tokens.find(e => e.name === token_name).checked;
  }

  protected fileUpload(files_path: string, type: string, tokens: any[]) {
    console.log("Upload file for Schema to " + files_path);
    this.commonService.uploadFiles(this.schemaId, type, this.uploadFiles)
      .subscribe( result => {
        console.log(result);

        if (type === "pattern") {
          this.commonService.schemaMining(files_path, this.schemaId, this.min_support, this.pattern_min, this.pattern_max, tokens)
          .subscribe( data => {
            this.patternList = data.pattern;
            this.patternLen = this.patternList.length;

            this.selectedList = data.selected;
            this.selectedLen = this.selectedList.length;
            console.log(data);
          });
        } else if (type === "test") {
          this.schemaService.updateFileListOfSchema(this.schemaId, this.uploadFiles[0].name)
            .subscribe( data => {
              this.fileList = data.file_list;
              let fileId = this.fileList.find(file => file.name === this.uploadFiles[0].name).id;
              this.selectFileForMarked = this.fileList.find(file => file.name === this.uploadFiles[0].name);
              console.log(this.uploadFiles[0].name + " upload success!");
              this.filesService.addFileInfo(data.schema_id, fileId, data.dtd)
                .subscribe(result => {
                  this.selectFileInfo = result;
                  this.pdfStructure = result.instance;
                  this.pdfPositionColor = result.position;
                  this.cd.detectChanges();
                  let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
                  for (let i = 0; i < json_viewer.length; i++) {
                    json_viewer[i].style.position = 'initial';
                  }
                  this.getAttributeListWithLevel(result.instance);
                  console.log(result);
                });

              let path = this.selectSchemaInfo.files_path + type;
              this.commonService.readTextFileOfPDF(path, this.uploadFiles[0].name, this.selectFileTypeForMarked)
                .subscribe(result => {
                  this.pdfText = result;
                  this.resetContent(this.pdfText);
                  console.log("Go to extract file");
                  let content: HTMLElement = document.getElementById("pdf");
                  if (this.selectMethodForMarked === 'FST') {
                    this.filesService.fileExtraction(this.selectFileInfo.schema_id, this.selectFileInfo.file_id, this.pdfStructure, content.outerHTML, this.selectSchemaInfo.mapping, this.mainAttrList, this.selectFileTypeForMarked)
                    .subscribe( result => {
                      this.pdfStructure = result.instance;
                      this.markTextContent(result.position);
                      this.cd.detectChanges();
                      let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
                      for (let i = 0; i < json_viewer.length; i++) {
                          json_viewer[i].style.position = 'initial';
                      }
                      console.log(result);
                    });
                  } else if (this.selectMethodForMarked === 'Langchain-OutputParsing') {
                      this.filesService.fileExtractionByLangChain(this.selectFileInfo.schema_id, this.selectFileInfo.file_id, this.pdfStructure, content.outerHTML, this.mainAttrList, 'LCOP')
                      .subscribe( result => {
                        this.pdfStructure = result.instance;
                        this.markTextContent(result.position);
                        this.cd.detectChanges();
                        let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
                        for (let i = 0; i < json_viewer.length; i++) {
                            json_viewer[i].style.position = 'initial';
                        }
                        console.log(result);
                      });
                    }
                });
            });
        }
      });
  }

  goAnalyze() {
    let tokens = JSON.parse(JSON.stringify(this.tokens));
    tokens.find(e => e.name === 'Limit pattern length').name = `Limit pattern length: ${this.pattern_min} ~ ${this.pattern_max}`;

    if (typeof this.schema.value == "object") {
      this.schemaId = this.schema.value.id;
      console.log("Exist Schema = " + this.schemaId);
      this.schemaService.updateSchema(this.schemaId, this.min_support, tokens)
      .subscribe(data => {
        this.fileUpload(data.files_path, "pattern", this.tokens);
        console.log(data);
      });
    } else {
      let schema = this.schema.value;
      if (this.schemaList !== undefined) {
        if (this.schemaList.find(s => s.name === schema)) {
          window.alert(schema + " is exist! Please enter another schema name.");
          return;
        }
      }

      console.log("New Schema = " + this.schemaId);
      this.schemaService.addSchema(this.userId, schema, this.min_support, tokens)
      .subscribe(data => {
        this.schemaId = data.schema_id;
        this.fileUpload(data.files_path, "pattern", JSON.parse(JSON.stringify(this.tokens)));
        console.log(data);
      });
    }
    console.log("Analyze by PrefixSpan." );
  }

  remove() {
    this.removedList.push(...this.selectPatterns);

    // 由 pattern list 移除選取的 pattern
    let pattern = this.patternList;
    this.patternList = [];
    pattern.forEach( p => {
      let index = this.removedList.indexOf(p);
      if (index === -1)
        this.patternList.push(p);
    });

    // 移除相似的pattern
    this.selectPatterns.forEach(s => {
      this.patternList.forEach(p => {
        let ratio = this.commonService.getSimilarity(p, s);
          if (ratio >= 70) {
            this.removedList.push(p);
          }
      });
    });

    pattern = this.patternList;
    this.patternList = [];
    pattern.forEach( p => {
      let index = this.removedList.indexOf(p);
      if (index === -1)
        this.patternList.push(p);
    });

    this.patternLen = this.patternList.length;
    this.removedLen = this.removedList.length;

    this.selectPatterns = [];
    this.cd.detectChanges();
  }

  restore(type: string) {
    // remove list to pattern list
    if (type === "remove") {
      this.patternList.push(...this.selectRemoved);

      // 由 removed list 移除選取的 pattern
      let remove = this.removedList;
      this.removedList = [];
      remove.forEach( p => {
        let index = this.patternList.indexOf(p);
        if (index === -1)
          this.removedList.push(p);
      });

      this.selectRemoved = [];
    }

    // select list to pattern list
    if (type === "select") {
      this.patternList.push(...this.selectSelected);

      // 由 selected list 移除選取的 pattern
      let select = this.selectedList;
      this.selectedList = [];
      select.forEach( p => {
        let index = this.patternList.indexOf(p);
        if (index === -1)
          this.selectedList.push(p);
      });

      this.selectSelected = [];
    }

    this.patternLen = this.patternList.length;
    this.removedLen = this.removedList.length;
    this.selectedLen = this.selectedList.length;
    this.cd.detectChanges();
  }

  select() {
    this.selectedList.push(...this.selectPatterns);

    // 由 pattern list 移除選取的 pattern
    let pattern = this.patternList;
    this.patternList = [];
    pattern.forEach( p => {
      let index = this.selectedList.indexOf(p);
      if (index === -1)
        this.patternList.push(p);
    });

    this.patternLen = this.patternList.length;
    this.selectedLen = this.selectedList.length;
    this.selectPatterns = [];
    this.cd.detectChanges();
  }

  goSave() {
    this.schemaService.updatePatternOfSchema(this.schemaId, this.selectedList)
      .subscribe(data => {
        console.log(data);
        console.log("Save success!");
        window.alert("Save success!");
        window.location.reload();
      });
  }

  getPatterns(schema: Schema) {
    this.schemaId = schema.id;
    this.schemaService.getPatterns(schema.id)
      .subscribe( data => {
        this.choosePatterns = data;
        });

    this.schemaService.getAttributes(schema.id)
      .subscribe(data => {
        this.attrList = data;
        this.selectPreAttr = this.attrList[0];
      });

    this.schemaService.getDtd(schema.id)
      .subscribe(data => {
        if (data === '') {
          this.schemaStructure = undefined;
        } else {
          this.schemaStructure = JSON.parse(data);
          this.cd.detectChanges();
          let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
          for (let i = 0; i < json_viewer.length; i++) {
            json_viewer[i].style.position = 'initial';
          }
        }
      });
    console.log("get " + schema.name + "'s attribute list");
  }

  addAttribute(attr: string) {
    if (this.attrList.length > 0 ) {
      if (this.attrList.find(s => s === attr)) {
        window.alert(attr + " is exist! Please enter another attribute.");
        return;
      }
    }

    this.schemaService.updateAttributeOfSchema(this.schemaId, attr)
      .subscribe(result => {
        console.log(result);
        this.schemaService.getAttributes(this.schemaId)
        .subscribe(data => {
          this.attrList = data;
        });
        this.attribute = '';
      });
    console.log("add attribute: " + attr);
  }

  addToSchema(selectAttr: string, selectDataType:string, selectLevel: Level, selectedPattern: string[], selectPreAttr: string) {
    let output: object = this.schemaStructure===undefined ? {} : this.schemaStructure;
    let pattern = selectedPattern.toString();
    let pList = [];
    if (selectDataType === 'String') {
      if (selectLevel.value === '2') {
        output[selectPreAttr] = output[selectPreAttr]===undefined ? {} : output[selectPreAttr];
        output[selectPreAttr][selectAttr] = pattern.replace(/,/g,'/');
      } else {
        output[selectAttr] = pattern.replace(/,/g,'/');
      }
    } else if (selectDataType === 'Array') {
      pattern = pattern.replace(/,/g,'/');
      pList.push(pattern);
      if (selectLevel.value === '2') {
        output[selectPreAttr] = output[selectPreAttr]===undefined ? {} : output[selectPreAttr];
        output[selectPreAttr][selectAttr] = pList;
      } else {
        output[selectAttr] = pList;
      }
    }
    this.selectedPattern = [];
    this.schemaStructure = JSON.parse(JSON.stringify(output));
    this.cd.detectChanges();
    let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
    for (let i = 0; i < json_viewer.length; i++) {
      json_viewer[i].style.position = 'initial';
    }
  }

  saveSchema(schema: object) {
    let dtd = JSON.stringify(schema)
    this.schemaService.updateDtdOfSchema(this.schemaId, dtd)
      .subscribe(data =>  {
        console.log(data);
        window.alert('Save success ');
      });
  }

  changeSchema(selectSchema: Schema): void {
    this.schemaService.getSchemaInfo(selectSchema.id)
      .subscribe( data => {
        this.schemaId = data.schema_id;
        this.selectSchemaInfo = data;
        this.fileList = data.file_list;
        console.log(this.selectSchemaInfo);
      });
    console.log(selectSchema);
  }

  changeMethod(selectMethod: string): void {
    console.log(selectMethod);
  }

  uploadFileTest(event): void {
    this.selectedFileTest = <File>event.target.files[0];
    let fileName = this.selectedFileTest.name;
    if (fileName.substring(fileName.lastIndexOf('.')) === '.pdf') {
      this.uploadFiles[0] = <File> this.selectedFileTest;
    } else {
      window.alert('Wrong file: ' + fileName);
    }

    if (this.fileList !== []) {
      if (this.fileList.find(s => s.name === fileName)) {
        window.alert(fileName + " is exist! Please enter another pdf file.");
        return;
      }
    }

    this.fileUpload(this.selectSchemaInfo.files_path, "test", null);
  }

  changePDFFile(fileInfo: FileInfo): void {
    let path = this.selectSchemaInfo.files_path + "test";
    this.commonService.readTextFileOfPDF(path, fileInfo.name, this.selectFileTypeForMarked)
      .subscribe(result => {
        this.pdfText = result;
        this.resetContent(this.pdfText);
        this.filesService.getFileInfo(this.selectSchemaInfo.schema_id, fileInfo.id)
          .subscribe(result => {
            this.selectFileInfo = result;
            this.pdfStructure = result.instance;
            this.pdfPositionColor = result.position;
            this.cd.detectChanges();
            let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
            for (let i = 0; i < json_viewer.length; i++) {
                json_viewer[i].style.position = 'initial';
            }
            this.getAttributeListWithLevel(result.instance);
            this.markTextContent(this.pdfPositionColor);
          });
      });
  }

  getSelectText() {
    const selected = window.getSelection();
    let anchor_node = selected.anchorNode.parentNode;
    let focus_node = selected.focusNode.parentNode;
    let startLine = parseInt(anchor_node.parentElement.id.split("-")[1], 10);
    let endLine = parseInt(focus_node.parentElement.id.split("-")[1], 10);
    let start = anchor_node["dataset"].value;
    let end = focus_node["dataset"].value;
    if (parseInt(start, 10) < parseInt(end, 10)) {
        end = (parseInt(end, 10) + 1).toString();
    } else {
        let temp = start;
        start = end;
        end = (parseInt(temp, 10) + 1).toString();
    }

    let lines = [];
    if (startLine === endLine) {
      let lineId = "line-" + startLine;
      lines.push(lineId);
    } else {
      if (startLine > endLine) {
        let temp = startLine;
        startLine = endLine;
        endLine = temp;
      }

      for (let i = startLine; i <= endLine; i++) {
        let lineId = "line-" + i;
        lines.push(lineId);
      }
    }

    for (let i = 0; i < lines.length; i++) {
      let p = document.getElementById(lines[i]);
      let children = Array.prototype.slice.call(p.childNodes);
      children.forEach(n => {
        if (n.localName === "button")
          p.removeChild(document.getElementById(n.id));
      })
    }

    this.selectedText = {
      text: selected.toString().replace(/\n/g, '')
                               .replace(/　/g, '')
                               .replace(/  /g, '')
                               .replace(/ /g, ''),
      lineId: lines,
      start: start,
      end: end
    };

    console.log(this.selectedText);
  }

  changeAttr(attr: AttrLevel) {
    this.selectAttrOfSub = "";
    this.subAttrList = attr.level2;
    if (this.subAttrList !== undefined) {
      if (this.subAttrList.length !== 0)
        this.subAttrDisplay = false;
    }
    console.log(attr);
  }

  addToStructure(mainAttr: AttrLevel, subAttr: string): void {
    if (this.selectedText["text"] === "")
      return;

    let pc = {
      lineId: this.selectedText["lineId"],
      start: this.selectedText["start"],
      end: this.selectedText["end"],
      color: mainAttr.color
    };
    if (subAttr === "") {
      if (typeof this.pdfStructure[mainAttr.level1] === 'object') {
        this.pdfStructure[mainAttr.level1].push(this.selectedText["text"]);
        this.pdfPositionColor[mainAttr.level1].push(JSON.stringify(pc));
      } else {
        this.pdfStructure[mainAttr.level1] = this.selectedText["text"];
        this.pdfPositionColor[mainAttr.level1] = JSON.stringify(pc);
      }
    } else {
      if (typeof this.pdfStructure[mainAttr.level1][subAttr] === 'object') {
        this.pdfStructure[mainAttr.level1][subAttr].push(this.selectedText["text"]);
        this.pdfPositionColor[mainAttr.level1][subAttr].push(JSON.stringify(pc));
      } else {
        this.pdfStructure[mainAttr.level1][subAttr] = this.selectedText["text"];
        this.pdfPositionColor[mainAttr.level1][subAttr] = JSON.stringify(pc);
      }
    }
    this.pdfStructure = JSON.parse(JSON.stringify(this.pdfStructure));
    this.pdfPositionColor = JSON.parse(JSON.stringify(this.pdfPositionColor));
    this.resetContent(this.pdfText);
    this.markTextContent(this.pdfPositionColor);
    this.cd.detectChanges();
    let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
    for (let i = 0; i < json_viewer.length; i++) {
        json_viewer[i].style.position = 'initial';
    }
    this.selectedText = {text: "", lineId:[], start: -1, end: -1};
  }

  saveFileStructure(): void {
    let content: HTMLElement = document.getElementById("pdf");
    this.filesService.updateStructureById(this.selectFileInfo.schema_id, this.selectFileInfo.file_id, this.pdfStructure, this.pdfPositionColor)
      .subscribe(result => {
        window.alert("Save completed");
        if (this.selectMethodForMarked === 'FST') {
          this.schemaService.learningRule(this.selectFileInfo.schema_id, this.selectFileInfo.file_id, this.pdfStructure, content.outerHTML, this.selectSchemaInfo.mapping, this.selectFileTypeForMarked)
          .subscribe( result => {
            console.log(result);
          });
        } else if (this.selectMethodForMarked === 'Langchain-OutputParsing') {
          this.schemaService.updatePatternsByLangchain(this.selectFileInfo.schema_id, this.pdfStructure, content.outerHTML)
          .subscribe( result => {
            console.log(result);
          });
        }
      });
  }

  removeValue(eleInfo: any) {
    let removeAttrAndPos = eleInfo.id;
    let attr = removeAttrAndPos.split("#")[0];
    let pos = removeAttrAndPos.split("#")[1];
    if(attr.match(RegExp("-"))) {
      let mainAttr = attr.split("-")[0];
      let subAttr = attr.split("-")[1];
      if (pos!=="99") {
        this.pdfStructure[mainAttr][subAttr].splice(pos, 1);
        this.pdfPositionColor[mainAttr][subAttr].splice(pos, 1);
      } else {
        this.pdfStructure[mainAttr][subAttr] = "";
        this.pdfPositionColor[mainAttr][subAttr] = "";
      }
    } else {
      if (pos!=="99") {
        this.pdfStructure[attr].splice(pos, 1);
        this.pdfPositionColor[attr].splice(pos, 1);
      } else {
        this.pdfStructure[attr] = "";
        this.pdfPositionColor[attr] = "";
      }
    }
    this.pdfStructure = JSON.parse(JSON.stringify(this.pdfStructure));
    this.pdfPositionColor = JSON.parse(JSON.stringify(this.pdfPositionColor));
    this.resetContent(this.pdfText);
    this.markTextContent(this.pdfPositionColor);
    this.cd.detectChanges();
    let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
    for (let i = 0; i < json_viewer.length; i++) {
        json_viewer[i].style.position = 'initial';
    }
    console.log(eleInfo);
  }

  protected getPatternAttr(dtd: string, lineText: string) {
    let pattern = "";
    let structure = JSON.parse(dtd);
    let text = lineText.split('　')[0];
    let key1 = Object.keys(structure);
    for (let i = 0; i < key1.length; i++) {
      if (typeof structure[key1[i]] === 'object'){
        if (Array.isArray(structure[key1[i]])) {
          if (structure[key1[i]].length !== 0) {
            let attrArray = structure[key1[i]][0].split('/');
            for (let a = 0; a < attrArray.length; a++) {
              let ratio = distance(attrArray[a], text);
              if (ratio < 1) {
                if (pattern === "")
                  pattern = key1[i];
                else
                  pattern = pattern + "/" + key1[i];
                break;
              }
            }
          }
        } else {
          let key2 = Object.keys(structure[key1[i]]);
          for (let j = 0; j < key2.length; j++) {
            if (Array.isArray(structure[key1[i]][key2[j]])) {
              if (structure[key1[i]][key2[j]].length !== 0) {
                let attrArray = structure[key1[i]][key2[j]][0].split('/');
                for (let a = 0; a < attrArray.length; a++) {
                  let ratio = distance(attrArray[a], text);
                  if (ratio < 1) {
                    if (pattern === "")
                      pattern = key1[i] + "." + key2[j];
                    else
                      pattern = pattern + "/" + key1[i] + "." + key2[j];
                    break;
                  }
                }
              }
            }
          }
        }
      } else {
        if (structure[key1[i]] === "")
          continue;
        let attrArray = structure[key1[i]].split('/');
        for (let a = 0; a < attrArray.length; a++) {
          let ratio = distance(attrArray[a], text);
          if (ratio < 1) {
            if (pattern === "")
              pattern = key1[i];
            else
              pattern = pattern + "/" + key1[i];
            break;
          }
        }
      }
    }

    return pattern;
  }

  protected resetContent(text: string) {
    text = text.replace(/ /g, '&nbsp')
               .replace(/</g, '&lt')
               .replace(/>/g, '&gt')
               .replace(/\\n/g, '<br/>')
               .replace(/\n/g, '<br/>')
    let content = text.split("<br/>");
    let textContent = document.getElementById('textContent');
    if (textContent.children.length > 0) {
      textContent.removeChild(document.getElementById("pdf"));
    }

    let pdfContent = document.createElement('div');
    pdfContent.id = "pdf";
    let dataIdx = 0;
    for (let i = 0; i < content.length; i++) {
      let pattern = "";
      if (content[i].length > 1) {
        pattern = this.getPatternAttr(this.selectSchemaInfo.dtd, content[i].replace('：', '：　'));
      }

      let lineContent = document.createElement('p');
      lineContent.id = "line-" + i;
      if (pattern !== "")
        lineContent.setAttribute('pattern', pattern);
      for (let j = 0; j < content[i].length; j++)
      {
        let span = document.createElement('span');
        span.innerHTML = content[i].charAt(j);
        span.dataset["value"] = String(dataIdx);
        span.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        dataIdx = dataIdx + 1;
        lineContent.appendChild(span);
      }
      pdfContent.appendChild(lineContent);
    }
    textContent.appendChild(pdfContent);
    this.cd.detectChanges();
  }

  protected getAttributeListWithLevel(structure: any) {
    this.mainAttrList = [];
    let attr = [];
    let option = {};
    let key1 = Object.keys(structure);
    for (let i = 0; i < key1.length; i++) {
      if (typeof structure[key1[i]] === 'object'){
        option = {
          "level1" : key1[i],
          "level2" : Object.keys(structure[key1[i]]),
          "color" : this.rgb_generator()
        };
      } else {
        option = {
          "level1" : key1[i],
          "color" : this.rgb_generator()
        };
      }
      attr.push(option);
    }
    this.mainAttrList = attr;
    console.log(this.mainAttrList);
  }

  protected rgb_generator() {
    let r = Math.floor(Math.random() * 256);
    let g = Math.floor(Math.random() * 256);
    let b = Math.floor(Math.random() * 256);
    return { r, g, b }
  }

  protected setRemoveBtn(attr: string, index: number) {
    let btn = document.createElement("button");
    btn.setAttribute('class', 'remove-btn mat-focus-indicator mat-icon-button mat-button-base');
    btn.setAttribute('mat-icon-button', '');
    btn.setAttribute('aria-label', 'Remove');
    btn.setAttribute('id', attr + '#' + index);
    btn.onclick = (e) => {
      this.removeValue(btn); // keyword 'this' is the instance in this scope
    }

    let icon = document.createElement("mat-icon");
    icon.innerHTML = "cancel";
    icon.setAttribute('role', 'img');
    icon.setAttribute('class', 'remove-icon mat-icon notranslate material-icons material-symbols-outlined');
    icon.setAttribute('aria-hidden', 'true');
    icon.setAttribute('data-mat-icon-type', 'font');
    btn.appendChild(icon);
    return btn;
  }

  protected markTextContent(pdfPC: any) {
    let key1 = Object.keys(pdfPC);
    for (let i = 0; i < key1.length; i++) {
      if (typeof pdfPC[key1[i]] === 'object'){
        if (Array.isArray(pdfPC[key1[i]])) {
          if (pdfPC[key1[i]].length !== 0) {
            for (let a = 0; a < pdfPC[key1[i]].length; a++) {
              let pc = JSON.parse(pdfPC[key1[i]][a]);
              let line = pc.lineId;
              let start = pc.start;
              let end = pc.end;
              let color = pc.color;
              let btn = this.setRemoveBtn(key1[i], a);
              let idx = parseInt(start);
              for (const l of line) {
                let p = document.getElementById(l);
                let children = p.children;
                for (let i = 0; i < p.childNodes.length; i++) {
                  let dataset = p.childNodes[i]["dataset"].value;
                  if (parseInt(dataset) >= end) break;
                  if (parseInt(dataset) === idx) {
                    children[i]["style"].backgroundColor = 'rgba(' + color["r"] + ',' + color["g"] + ',' +
                          color["b"] + ',' + 0.3 + ')';
                    idx = idx + 1;
                  }
                  if (parseInt(dataset) === parseInt(start))
                    p.insertBefore(btn,children[i]);
                }
              }
            }
          }
        } else {
          let key2 = Object.keys(pdfPC[key1[i]]);
          for (let j = 0; j < key2.length; j++) {
            if (Array.isArray(pdfPC[key1[i]][key2[j]])) {
              if (pdfPC[key1[i]][key2[j]].length !== 0) {
                for (let a = 0; a < pdfPC[key1[i]][key2[j]].length; a++) {
                  let pc = JSON.parse(pdfPC[key1[i]][key2[j]][a]);
                  let line = pc.lineId;
                  let start = pc.start;
                  let end = pc.end;
                  let color = pc.color;
                  let id = key1[i] + "-" + key2[j];
                  let btn = this.setRemoveBtn(id, a);
                  let idx = parseInt(start);
                  for (const l of line) {
                    let p = document.getElementById(l);
                    let children = p.children;
                    for (let i = 0; i < p.childNodes.length; i++) {
                      let dataset = p.childNodes[i]["dataset"].value;
                      if (parseInt(dataset) >= end) break;
                      if (parseInt(dataset) === idx) {
                        children[i]["style"].backgroundColor = 'rgba(' + color["r"] + ',' + color["g"] + ',' +
                              color["b"] + ',' + 0.3 + ')';
                        idx = idx + 1;
                      }
                      if (parseInt(dataset) === parseInt(start))
                        p.insertBefore(btn,children[i]);
                    }
                  }
                }
              }
            } else {
              if (pdfPC[key1[i]][key2[j]] === "")
                continue;
              let pc = JSON.parse(pdfPC[key1[i]][key2[j]]);
              let line = pc.lineId;
              let start = pc.start;
              let end = pc.end;
              let color = pc.color;
              let id = key1[i] + "-" + key2[j];
              let btn = this.setRemoveBtn(id, 99);
              let idx = parseInt(start);

              for (const l of line) {
                let p = document.getElementById(l);
                let children = p.children;
                for (let i = 0; i < p.childNodes.length; i++) {
                  let dataset = p.childNodes[i]["dataset"].value;
                  if (parseInt(dataset) >= end) break;
                  if (parseInt(dataset) === idx) {
                    children[i]["style"].backgroundColor = 'rgba(' + color["r"] + ',' + color["g"] + ',' +
                          color["b"] + ',' + 0.3 + ')';
                    idx = idx + 1;
                  }
                  if (parseInt(dataset) === parseInt(start))
                    p.insertBefore(btn,children[i]);
                }
              }
            }
          }
        }
      } else {
        if (pdfPC[key1[i]] === "")
          continue;
        let pc = JSON.parse(pdfPC[key1[i]]);
        let line = pc.lineId;
        let start = pc.start;
        let end = pc.end;
        let color = pc.color;
        let btn = this.setRemoveBtn(key1[i], 99);
        let idx = parseInt(start);

        for (const l of line) {
          let p = document.getElementById(l);
          let children = p.children;
          for (let i = 0; i < p.childNodes.length; i++) {
            let dataset = p.childNodes[i]["dataset"].value;
            if (parseInt(dataset) >= end) break;
            if (parseInt(dataset) === idx) {
              children[i]["style"].backgroundColor = 'rgba(' + color["r"] + ',' + color["g"] + ',' +
                    color["b"] + ',' + 0.3 + ')';
              idx = idx + 1;
            }
            if (parseInt(dataset) === parseInt(start))
              p.insertBefore(btn,children[i]);
          }
        }
      }
    }
    this.cd.detectChanges();
  }
}

