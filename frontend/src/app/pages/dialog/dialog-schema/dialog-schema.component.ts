import {AfterViewInit, Component, Inject, OnInit} from "@angular/core";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

class DialogData {
  title: string;
  content: string;
}

@Component({
  selector: 'app-dialog-schema',
  templateUrl: 'dialog-schema.component.html',
})
export class DialogSchemaComponent implements AfterViewInit {
  constructor(
    public dialogRef: MatDialogRef<DialogSchemaComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData,
  ) {}

  ngAfterViewInit() {
    let json_viewer = document.getElementsByClassName("toggler") as HTMLCollectionOf<HTMLElement>;
    for (let i = 0; i < json_viewer.length; i++) {
        json_viewer[i].style.position = 'initial';
        json_viewer[i].style.display = 'initial';
        json_viewer[i].style.marginRight = '8px';
    }
  }
}
