import {ChangeDetectorRef, Component, OnInit} from "@angular/core";
import {FormControl, Validators} from "@angular/forms";
import {map, Observable, startWith} from "rxjs";
import {UserService} from "../@core/service/user.service";
import {MatDialog} from "@angular/material/dialog";
import {DialogSchemaComponent} from "./dialog/dialog-schema/dialog-schema.component";
import {CommonService} from "../@core/service/common.service";
import {SchemaService} from "../@core/service/schema.service";
import {Schema} from "../@core/model/user.model";
import {Level} from "../@core/model/schema.model";

@Component({
  selector: 'app-pages',
  templateUrl: './pages.component.html',
  styleUrls: ['./pages.component.scss'],
  providers: [UserService, SchemaService, CommonService]
})
export class PagesComponent implements OnInit{

  constructor( private cd: ChangeDetectorRef,
               private userService:UserService,
               private schemaService: SchemaService,
               private commonService: CommonService,
               public dialog: MatDialog ) { }

  tabIdx: number = 0;
  userId: string = '';
  schemaId: string = '';
  schema = new FormControl<Schema>(null, [Validators.required]);
  files = new FormControl<string>('', [Validators.required]);
  schemaList: Schema[];
  filteredSchemaList: Observable<Schema[]>;
  selectedSchema = null;
  selectedFiles: File[];
  uploadFiles: File[] = [];

  schemaOpenState = false;
  markedOpenState = false;

  min_support: number = 0.1;
  pattern_min: number = 2;
  pattern_max: number = 5;

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

  ngOnInit() {
    console.log(this.schemaStructure);
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
    this.schemaService.getSchema(this.selectedSchema)
      .subscribe( data => {
        let schemaStructure = JSON.parse(data);
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

  protected fileUpload(files_path: string, tokens: any[]) {
    console.log("Upload file for Schema to " + files_path);
    this.commonService.uploadFiles(files_path, this.uploadFiles)
      .subscribe( result => {
        console.log(result);

        this.commonService.schemaMining(files_path, this.schemaId, this.min_support, this.pattern_min, this.pattern_max, tokens)
          .subscribe( data => {
            this.patternList = data.pattern;
            this.patternLen = this.patternList.length;

            this.selectedList = data.selected;
            this.selectedLen = this.selectedList.length;
            console.log(data);
          });

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
        this.fileUpload(data.files_path, this.tokens);
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
        this.fileUpload(data.files_path, tokens);
        console.log(data);
      });
    }

    console.log("Analyze by PrefixSpan. " );
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
        output[selectPreAttr][selectAttr] = pattern.replace(',','/');
      } else {
        output[selectAttr] = pattern.replace(',','/');
      }
    } else if (selectDataType === 'Array') {
      pattern = pattern.replace(',','/');
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
  }

  saveSchema(schema: object) {
    let dtd = JSON.stringify(schema)
    this.schemaService.updateDtdOfSchema(this.schemaId, dtd)
      .subscribe(data =>  {
        console.log(data);
      });
  }

  // someComplete(): boolean {
  //   if (this.tokens == null) {
  //     return false;
  //   }
  //   return this.tokens.filter(t => t.completed).length > 0 && !this.allComplete;
  // }
  //
  // setAll(selected: boolean) {
  //   this.allComplete = selected;
  //   if (this.tokens == null) {
  //     return;
  //   }
  //   this.tokens.forEach(t => (t.completed = selected));
  // }

  // updateAllComplete() {
  //   this.allComplete = this.tokens != null && this.tokens.every(t => t.completed);
  // }
}

