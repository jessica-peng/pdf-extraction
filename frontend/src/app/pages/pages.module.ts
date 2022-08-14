import {CUSTOM_ELEMENTS_SCHEMA, NgModule} from "@angular/core";
import {PagesComponent} from "./pages.component";
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {MatFormFieldModule} from "@angular/material/form-field";
import {BrowserModule} from "@angular/platform-browser";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";
import {MatSelectModule} from "@angular/material/select";
import {MatButtonModule} from "@angular/material/button";
import {MatCardModule} from "@angular/material/card";
import {MatTabsModule} from "@angular/material/tabs";
import {MatInputModule} from "@angular/material/input";
import {MatAutocompleteModule} from "@angular/material/autocomplete";
import {CommonModule} from "@angular/common";
import {MatExpansionModule} from "@angular/material/expansion";
import {MatCheckboxModule} from "@angular/material/checkbox";
import {MatIconModule} from "@angular/material/icon";
import {MatTooltipModule} from "@angular/material/tooltip";
import {MatListModule} from "@angular/material/list";
import {HttpClientModule} from "@angular/common/http";
import {DialogSchemaComponent} from "./dialog/dialog-schema/dialog-schema.component";
import {MatDialogModule} from "@angular/material/dialog";
import { NgxJsonViewerModule } from "ngx-json-viewer";

// @ts-ignore
@NgModule({
  imports: [
    CommonModule,
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    NgxJsonViewerModule,
    MatFormFieldModule,
    MatCardModule,
    MatSelectModule,
    MatButtonModule,
    MatTabsModule,
    MatInputModule,
    MatAutocompleteModule,
    MatExpansionModule,
    MatCheckboxModule,
    MatTooltipModule,
    MatIconModule,
    MatListModule,
    MatDialogModule,
    MatSelectModule
  ],
  declarations: [
    PagesComponent,
    DialogSchemaComponent
  ],
  schemas:[CUSTOM_ELEMENTS_SCHEMA]
})
export class PagesModule { }
