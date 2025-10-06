# Software ACS project: Stenosis Annotations.
# Core Function for the LabelACS, the annotated bbx can be editable to resize and position changing.
# Developer: MA, Kochi University of Technology. 256013s@gs.kochi-tech.ac.jp
# Python, PyQt, Opencv.
# Core Function for Annotations.
# Beta version 0.1.

import os
import sys
import cv2
import yaml
from PySide6.QtCore import Qt, Slot, QRectF, QRect, QPoint, QObject, Signal
from PySide6.QtWidgets import (QMainWindow, QDialog, QLabel, 
                               QWidget, QPushButton, QVBoxLayout, 
                               QFileDialog, QMessageBox, QGraphicsView, 
                               QGraphicsScene, QToolBar, QApplication,
                               QGraphicsRectItem, QGraphicsItem, QRubberBand,
                               QGraphicsPixmapItem)
from PySide6.QtGui import (QPixmap, QIcon, QAction, QPainter, QPen, QMouseEvent, 
                           QBrush, QPainterPath, QColor, QImage)

class label_main(QMainWindow):
    def __init__(self, resize_info, save_root):
        super().__init__()
        self.setWindowTitle("ACS annotation, 簡単に使える")
        self.setWindowIcon(QIcon('./logo/label_acs.jpg'))
        self.test_UI()

        self.resize_info = resize_info
        self.save_root = save_root
        self.init = 0
        self.current = 0
        self.end = 0

    def test_UI(self):
        self.anno_scene = QGraphicsScene(self)
        pixmap = QPixmap("./logo/label_acs.jpg")
        image_item = QGraphicsPixmapItem(pixmap.scaled(512, 512, 
                                            Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation))
        self.anno_scene.addItem(image_item)

        # To set the view size for image
        self.view = AnnotedView(self.anno_scene, image_item, False)
        img_area = image_item.boundingRect()
        img_width = img_area.width()
        img_height = img_area.height()
        self.view.resize(img_width, img_height)

        select_button = QPushButton('動画データのファルダを選んでください')
        select_button.clicked.connect(self.vid_root)
        
        previous_button = QPushButton('前に イメージ')
        previous_button.clicked.connect(self.prev_img)

        save_button = QPushButton('動画のアノテーションは 確認してから それぞれに 保存してください')
        save_button.clicked.connect(self.save_anno)

        next_button = QPushButton('次に イメージ')
        next_button.clicked.connect(self.next_img)

        exit_button = QPushButton('退出')
        exit_button.clicked.connect(self.close_window)
        
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(select_button)
        layout.addWidget(previous_button)
        layout.addWidget(save_button)
        layout.addWidget(next_button)
        layout.addWidget(exit_button)

        sreen_show = QWidget()
        sreen_show.setLayout(layout)
        self.setCentralWidget(sreen_show)

    @Slot()
    def vid_root(self):
        dir_dialog = QFileDialog.getExistingDirectory(self, "select a directory")
        if dir_dialog:
            print("directory of selected video for the annotations:", dir_dialog)
        self.selected_vid_pth = dir_dialog
        self.imgList_vid = os.listdir(self.selected_vid_pth)
        nums_imgs = len(self.imgList_vid)
        self.end = nums_imgs-1
        self.init_img = os.path.join(self.selected_vid_pth, self.imgList_vid[0])
        self.init_img = self.init_img.replace('\\', '/')

        pixmap = QPixmap(self.init_img)
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.anno_scene.addItem(self.image_item)
        self.view.annoing_label = True

    @Slot()
    def prev_img(self):
        if self.current == self.init:
            QMessageBox.information(QDialog(), '注意', f'最初の画像:{self.imgList_vid[self.current]}')
        else:
            self.current -= 1
        self.init_img = os.path.join(self.selected_vid_pth, self.imgList_vid[self.current])
        self.init_img = self.init_img.replace('\\', '/')
        pixmap = QPixmap(self.init_img)
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.anno_scene.addItem(self.image_item)

        img_name = self.init_img.split('/')[-1]
        patient_ID = img_name.split('_')[0]
        video_ID = img_name.split('-')[0]
        init_annIfo = os.path.join(self.save_root, patient_ID, video_ID, img_name.split('.')[0]+'.txt')


    @Slot()
    def next_img(self):
        if self.current == self.end:
            QMessageBox.information(QDialog(), '注意', f'最後の画像:{self.imgList_vid[self.current]}')
        else:
            self.current += 1
        self.init_img = os.path.join(self.selected_vid_pth, self.imgList_vid[self.current])
        self.init_img = self.init_img.replace('\\', '/')
        
        pixmap = QPixmap(self.init_img)
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.anno_scene.addItem(self.image_item)

        img_name = self.init_img.split('/')[-1]
        patient_ID = img_name.split('_')[0]
        video_ID = img_name.split('-')[0]
        init_annIfo = os.path.join(self.save_root, patient_ID, video_ID, img_name.split('.')[0]+'.txt')

    @Slot()
    def save_anno(self):
        img_pth = self.init_img
        for i, bbx in enumerate(self.view.annBBxes):

            topLx = bbx.rect().x()
            topLy = bbx.rect().y()
            width = bbx.rect().width()
            height = bbx.rect().height()

            bottomRx = topLx+width
            bottomRy = topLy+height

            center_x = topLx+width/2
            center_y = topLy+height/2
            
            if width >= height:
                length = int(width)
            else:
                length = int(height)

            reLx = round(center_x-(length/2))
            reRy = round(center_y-(length/2))

            img_name = img_pth.split('/')[-1]
            patient_ID = img_name.split('_')[0]
            video_ID = img_name.split('-')[0]
            sv_pth = os.path.join(self.save_root, patient_ID, video_ID)
            sv_pth = sv_pth.replace('\\', '/')
            if not os.path.exists(sv_pth):
                os.makedirs(sv_pth)
            sv_img_pth = os.path.join(sv_pth, img_name)

            ori_img = cv2.imread(img_pth)
            crop_img = ori_img[reRy:reRy+length, reLx:reLx+length]       #opencv --> crop(y1:y2, x1:x2) 
            resize_img = cv2.resize(crop_img, (64, 64))
            cv2.imwrite(sv_img_pth, resize_img)

            ann_txt = os.path.join(sv_pth, img_name.split('.')[0]+'.txt')
            acs_cls = ''.join(filter(lambda x: not x.isdigit(), patient_ID))
            bbox_infos = {'TopLx':topLx, 
                        'TopLy':topLy,
                        'BottomRx':bottomRx, 
                        'BottomRy':bottomRy, 
                        'ACS_class':acs_cls}
            bbox_infos = yaml.dump(bbox_infos, allow_unicode=True)
            with open(ann_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(bbox_infos)

    @Slot()
    def close_window(self):
        self.close()

class AnnotedView(QGraphicsView):
    # Using RubberBand as the Interaction with custom, 2025/10/04 
    # author: krlab-ma, 256013s@gs.kochi-tech.ac.jp
    def __init__(self, scene, image_item, annoing_label):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.image_item = image_item
        self.img_rect = image_item.boundingRect()
        self.start_pos = None
        self.new_anno = None
        self.labeling = False
        self.annBBxes = []
        self.annoing_label = annoing_label

    def mousePressEvent(self, event):
        if self.annoing_label is True and event.button() == Qt.MouseButton.LeftButton:
            # if not self.img_rect.contains(current_pos):
            #     return 
            bbx_item = self.itemAt(event.pos())
            if isinstance(bbx_item, Editable2bbx):
                self.labeling = False
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            else:
                self.start_pos = self.mapToScene(event.pos().x(), event.pos().y())
                self.labeling = True
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.annoing_label is True and event.button() == Qt.MouseButton.LeftButton:
            if self.labeling and self.start_pos is not None:
                end_pos = self.mapToScene(event.pos().x(), event.pos().y())
                rubber_bbx = QRectF(self.start_pos, end_pos).normalized()

                img_rect = self.image_item.boundingRect()
                selected_bbx = rubber_bbx.intersected(img_rect)

                if selected_bbx.isValid() and selected_bbx.width()>5 and selected_bbx.height()>5:
                    bbx_item = Editable2bbx(selected_bbx, img_rect)
                    bbx_item.setAcceptHoverEvents(True)
                    self.scene().addItem(bbx_item)
                    self.annBBxes.append(bbx_item)

        super().mouseReleaseEvent(event)

class Editable2bbx(QObject, QGraphicsRectItem):
    cursors_size = 6
    cursors = {'tl':Qt.CursorShape.SizeFDiagCursor, 'tr':Qt.CursorShape.SizeBDiagCursor,
                'tm':Qt.CursorShape.SizeVerCursor, 'bm':Qt.CursorShape.SizeVerCursor,
                'bl':Qt.CursorShape.SizeBDiagCursor, 'br':Qt.CursorShape.SizeFDiagCursor,
                'lm':Qt.CursorShape.SizeHorCursor, 'rm':Qt.CursorShape.SizeHorCursor}
    anno_moved = Signal(QRectF)

    def __init__(self, rect=QRectF, img_rect=QRectF):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, rect)
        self.setPen(QPen(QColor(255, 0, 0), 2))
        transparentC = QColor(255, 255, 0, 28)
        brushC = QBrush(transparentC)
        self.setBrush(brushC)
        self.setFlags(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable 
                    | QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.edit_cursors = {}
        self.crusors_selected = False
        self.bbx_selected = None

        self.img_rect = img_rect

        self.update_cursors()
    
    def boundingRect(self):
        raduis = Editable2bbx.cursors_size
        return self.rect().adjusted(-raduis, -raduis, raduis, raduis)
    
    def update_cursors(self):
        bbx_item = QGraphicsRectItem(self.rect())
        bbx_item.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))
        bbx = self.rect()
        raduis = Editable2bbx.cursors_size
        self.edit_cursors = {
                            "tl": QRectF(bbx.left() - raduis/2, bbx.top() - raduis/2, raduis, raduis),
                            "tr": QRectF(bbx.right() - raduis/2, bbx.top() - raduis/2, raduis, raduis),
                            "bl": QRectF(bbx.left() - raduis/2, bbx.bottom() - raduis/2, raduis, raduis),
                            "br": QRectF(bbx.right() - raduis/2, bbx.bottom() - raduis/2, raduis, raduis),
                            "tm": QRectF(bbx.center().x() - raduis/2, bbx.top() - raduis/2, raduis, raduis),
                            "bm": QRectF(bbx.center().x() - raduis/2, bbx.bottom() - raduis/2, raduis, raduis),
                            "lm": QRectF(bbx.left() - raduis/2, bbx.center().y() - raduis/2, raduis, raduis),
                            "rm": QRectF(bbx.right() - raduis/2, bbx.center().y() - raduis/2, raduis, raduis)
                            }

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            for cursor in self.edit_cursors.values():
                painter.drawRect(cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for vertex, sign in self.edit_cursors.items():
                if sign.contains(event.pos()):
                    self.bbx_selected = vertex
                    break
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.bbx_selected is not None:
            edit_pos = event.pos()
            bbx = self.rect()
            if self.bbx_selected == 'tl':
                bbx.setTopLeft(edit_pos)
            elif self.bbx_selected == 'tr':
                bbx.setTopRight(edit_pos)
            elif self.bbx_selected == 'bl':
                bbx.setBottomLeft(edit_pos)
            elif self.bbx_selected == 'br':
                bbx.setBottomRight(edit_pos)
            elif self.bbx_selected == 'lm':
                bbx.setLeft(edit_pos.x())
            elif self.bbx_selected == 'rm':
                bbx.setRight(edit_pos.x())
            elif self.bbx_selected == 'tm':
                bbx.setTop(edit_pos.y())
            elif self.bbx_selected == 'bm':
                bbx.setBottom(edit_pos.y())
            self.setRect(bbx.normalized())        # !!dont forget this line to update the bbx after editing!!
            self.update_cursors()
            self.update()
            self.anno_moved.emit(self.rect())
        else:
            super().mouseMoveEvent(event)
            self.anno_moved.emit(self.rect())

    def mouseReleaseEvent(self, event):
        self.bbx_selected = None
        self.anno_moved.emit(self.rect())
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        if self.isSelected():
            for vertex, sign in self.edit_cursors.items():
                if sign.contains(event.pos()):
                    self.setCursor(self.cursors[vertex])
                    return
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverMoveEvent(event)

if __name__ == "__main__":
    save_root = 'D:/test_dataset/Save_Anno'
    resize_info = 64
    app = QApplication(sys.argv)
    window = label_main(resize_info, save_root)
    window.show()
    sys.exit(app.exec())