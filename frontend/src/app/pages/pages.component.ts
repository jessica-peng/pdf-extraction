import {Component, OnInit} from "@angular/core";
import {FormControl, Validators} from "@angular/forms";
import {map, Observable, startWith} from "rxjs";
import {HttpClient} from "@angular/common/http";

@Component({
  selector: 'app-pages',
  templateUrl: './pages.component.html',
  styleUrls: ['./pages.component.scss']
})
export class PagesComponent implements OnInit{

  constructor(private httpClient: HttpClient) {
  }

  categoryList = ['裁判書', '起訴書'];
  tokens = [
    {name: 'Basic symbol', completed: false},
    {name: 'Number', completed: false},
    {name: 'Duplicate characters', completed: false},
    {name: 'Limit pattern length', completed: false}
  ]

  patternList: string[] = ['pattern 1', 'pattern 2', 'pattern 3', 'pattern 4', 'pattern 5', 'pattern 6', 'pattern 7', 'pattern 8', 'pattern 9', 'pattern 10'];
  selectedFiles: File[];
  selectedCategory = null;
  category = new FormControl<string>('', [Validators.required]);
  files = new FormControl<string>('', [Validators.required]);
  filteredCategoryList: Observable<string[]>;
  allComplete: boolean = false;
  pattern_min: number = 2;
  pattern_max: number = 5;
  schemaOpenState = false;
  markedOpenState = false;

  serverData: JSON;

  ngOnInit() {
    this.filteredCategoryList = this.category.valueChanges.pipe(
      startWith(''),
      map(value => {
        return this.categoryList.slice();
      }),
    );

    this.schemaOpenState = true;
  }

  displaySchema() {
    this.httpClient.get('http://127.0.0.1:5002/').subscribe(data => {
      this.serverData = data as JSON;
      console.log(this.serverData);
    })
  }

  getPatterns(category: string) {
    console.log("get " + category + "'s patterns");
  }

  onFileInput(event): void {
    this.selectedFiles = <File[]>event.target.files;
    let filesName = '';
    let much: boolean = this.selectedFiles.length > 2;
    for (let i = 0; i < this.selectedFiles.length; i++) {
      if (i == 0) {
        filesName = event.target.files[i].name;
      } else {
        filesName = filesName + ',' + event.target.files[i].name;
      }

      if (i == 2)
        break;
    }
    if (much) {
        filesName = filesName + '...';
    }
    this.files.setValue(filesName);
  }

  someComplete(): boolean {
    if (this.tokens == null) {
      return false;
    }
    return this.tokens.filter(t => t.completed).length > 0 && !this.allComplete;
  }

  setAll(completed: boolean) {
    this.allComplete = completed;
    if (this.tokens == null) {
      return;
    }
    this.tokens.forEach(t => (t.completed = completed));
  }

  updateAllComplete() {
    this.allComplete = this.tokens != null && this.tokens.every(t => t.completed);
  }

  goAnalyze() {
    console.log("Analyze by PrefixSpan. " );
  }

  goSave() {
    console.log("Save!" );
  }
}
